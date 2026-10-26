
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.db import transaction

from .models import Notification
from messaging.models import Message
from verification.models import ContactRequest


@login_required
def list_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications
        }
    )


@login_required
@require_POST
def mark_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    user_id = request.user.pk

    def send_notification_update():
        from config.socketio import emit_from_django

        emit_from_django(
            "notifications_read",
            {
                "unread_count": 0
            },
            user_id
        )

    transaction.on_commit(send_notification_update)

    messages.success(
        request,
        "All notifications marked as read."
    )

    return redirect(
        reverse("inbox") + "?tab=notifications"
    )


@login_required
@never_cache
def unread_summary(request):

    unread_messages = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    pending_requests = ContactRequest.objects.filter(
        receiver=request.user,
        status="pending"
    ).count()

    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    inbox_badge_count = (
        unread_messages + pending_requests
    )

    return JsonResponse({
        "unread_messages": unread_messages,
        "pending_requests": pending_requests,
        "unread_notifications": unread_notifications,
        "inbox_badge_count": inbox_badge_count,
    })
