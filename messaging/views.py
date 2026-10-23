
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)
from django.urls import reverse
from django.views.decorators.http import require_POST

from verification.models import ContactRequest
from notifications.models import Notification
from notifications.services import notify

from .models import Message
from .forms import MessageForm


# =========================================
# GET USER CONVERSATIONS
# =========================================

def user_conversations(user):
    return ContactRequest.objects.filter(
        Q(sender=user) | Q(receiver=user)
    )


# =========================================
# MESSENGER STYLE INBOX
# =========================================

@login_required
def inbox(request):
    user = request.user

    # Find the latest message in each conversation.
    latest_message = (
        Message.objects
        .filter(request_id=OuterRef("pk"))
        .order_by("-created_at", "-pk")
    )

    # Get all conversations for the current user.
    conversations = (
        user_conversations(user)
        .select_related(
            "post",
            "sender",
            "receiver"
        )
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(
                    messages__receiver=user,
                    messages__is_read=False
                )
            ),
            latest_text=Subquery(
                latest_message.values("content")[:1]
            ),
            latest_at=Subquery(
                latest_message.values("created_at")[:1]
            )
        )
        .order_by("-created_at", "-pk")
    )

    # Notification history
    recent_notifications = (
        Notification.objects
        .filter(user=user)
        .select_related("post")
        .order_by("-created_at")[:20]
    )

    # Recent requests, both sent and received.
    recent_requests = (
        user_conversations(user)
        .select_related(
            "post",
            "sender",
            "receiver"
        )
        .order_by("-created_at")[:20]
    )

    # Currently selected conversation.
    active_chat = None
    chat_messages = []

    chat_id = request.GET.get("chat")

    if chat_id:
        active_chat = get_object_or_404(
            user_conversations(user).select_related(
                "post",
                "sender",
                "receiver"
            ),
            pk=chat_id
        )
    else:
        active_chat = conversations.first()

    
    if active_chat:

        # Mark messages as read only when the user
        # explicitly opens a conversation.
        if chat_id:
            Message.objects.filter(
                request=active_chat,
                receiver=user,
                is_read=False
            ).update(is_read=True)

        # Load messages in chronological order.
        chat_messages = (
            active_chat.messages
            .select_related("sender", "receiver")
            .order_by("created_at", "pk")
        )

        # Refresh conversation unread counters.
        conversations = list(conversations)

        if chat_id:
            for item in conversations:
                if item.pk == active_chat.pk:
                    item.unread_count = 0


        # Refresh current chat's unread count
        # for the left-side conversation list.
        conversations = list(conversations)

        for item in conversations:
            if item.pk == active_chat.pk:
                item.unread_count = 0

        # Get messages in chronological order.
        chat_messages = (
            active_chat.messages
            .select_related("sender", "receiver")
            .order_by("created_at", "pk")
        )

    return render(
        request,
        "messaging/inbox.html",
        {
            "conversations": conversations,
            "active_chat": active_chat,
            "chat_messages": chat_messages,
            "recent_notifications": recent_notifications,
            "recent_requests": recent_requests,
            "is_owner": (
                active_chat is not None
                and active_chat.receiver_id == user.id
            ),
        }
    )


# =========================================
# STANDALONE CONVERSATION
# =========================================

@login_required
def conversation(request, pk):

    obj = get_object_or_404(
        user_conversations(request.user)
        .select_related(
            "post",
            "sender",
            "receiver"
        ),
        pk=pk
    )

    # Mark received messages as read.
    obj.messages.filter(
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    chat_messages = (
        obj.messages
        .select_related("sender", "receiver")
        .order_by("created_at", "pk")
    )

    return render(
        request,
        "messaging/conversation.html",
        {
            "conversation": obj,
            "chat_messages": chat_messages,
            "form": MessageForm(),
            "is_owner": (
                obj.receiver_id == request.user.id
            ),
        }
    )


# =========================================
# SEND MESSAGE
# =========================================

@login_required
@require_POST
def send(request, pk):

    obj = get_object_or_404(
        user_conversations(request.user)
        .select_related(
            "post",
            "sender",
            "receiver"
        ),
        pk=pk
    )

    # SECURITY:
    # Messaging is only allowed after approval.
    if obj.status != "approved":

        messages.error(
            request,
            "This chat is locked until the "
            "contact request is approved."
        )

        return redirect(
            f"{reverse('inbox')}?chat={obj.pk}"
        )

    form = MessageForm(request.POST)

    if form.is_valid():

        msg = form.save(commit=False)

        msg.request = obj
        msg.sender = request.user

        # Identify the message receiver.
        if request.user.id == obj.sender_id:
            msg.receiver = obj.receiver
        else:
            msg.receiver = obj.sender

        msg.save()

        # Store notification in the database.
        notify(
            msg.receiver,
            f"New message from {request.user.username} "
            f'about "{obj.post.caption}".',
            obj.post
        )

    else:
        messages.error(
            request,
            "Please enter a valid message."
        )

    # Return to the selected conversation
    # inside the Messenger-style Inbox.
    return redirect(
        f"{reverse('inbox')}?chat={obj.pk}"
    )


# =========================================
# MARK CONVERSATION MESSAGES AS READ
# =========================================

@login_required
@require_POST
def mark_conversation_read(request, pk):

    conversation = get_object_or_404(
        user_conversations(request.user),
        pk=pk
    )

    # Only mark incoming messages as read.
    updated = Message.objects.filter(
        request=conversation,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({
        "success": True,
        "conversation_id": conversation.pk,
        "marked_read": updated
    })
