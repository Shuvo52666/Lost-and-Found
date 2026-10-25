
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from newsfeed.views import accessible_post
from notifications.services import notify
from config.socketio import emit_from_django

from .models import ContactRequest
from .forms import QuestionForm


# =========================================
# HELPER: OPEN SELECTED CHAT IN MAIN INBOX
# =========================================

def redirect_to_inbox_chat(contact_request_id):
    """
    Opens the main Messenger Inbox with the
    requested ContactRequest conversation selected.

    Example:
        /inbox/?chat=5
    """
    return redirect(
        f"{reverse('inbox')}?chat={contact_request_id}"
    )


# =========================================
# ADD VERIFICATION QUESTION
# =========================================

@login_required
def add_question(request, pk):

    post = accessible_post(request.user, pk)

    # Only the post owner can add questions.
    if post.user_id != request.user.id:
        raise Http404()

    form = QuestionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        obj = form.save(commit=False)
        obj.post = post
        obj.save()

        messages.success(
            request,
            "Verification question added."
        )

        return redirect("post_detail", pk=pk)

    return render(
        request,
        "generic_form.html",
        {
            "form": form,
            "heading": "Add verification question",
            "submit_label": "Add question",
        }
    )


# =========================================
# SEND CONTACT REQUEST
# =========================================

@login_required
def contact(request, pk):

    post = accessible_post(request.user, pk)

    # Users cannot contact themselves.
    if post.user_id == request.user.id:
        raise Http404()

    # An existing request should always open its
    # existing conversation instead of creating another.
    previous = ContactRequest.objects.filter(
        post=post,
        sender=request.user
    ).first()

    if previous:
        return redirect_to_inbox_chat(previous.pk)

    # New requests cannot be created for closed posts.
    if post.status != "open":
        raise Http404()

    # Get verification questions for this post.
    questions = list(
        post.verification_questions.order_by("id")
    )

    if request.method == "POST":

        answers = []
        errors = []

        # -----------------------------------------
        # COLLECT VERIFICATION ANSWERS
        # -----------------------------------------

        if questions:

            for question in questions:

                field_name = f"answer_{question.pk}"

                answer = request.POST.get(
                    field_name, ""
                ).strip()

                if not answer:
                    errors.append(
                        "Please answer every verification question."
                    )
                    break

                answers.append(
                    f"Q: {question.question}\nA: {answer}"
                )

        else:

            # If no verification questions exist,
            # require an initial contact message.
            answer = request.POST.get(
                "message", ""
            ).strip()

            if not answer:
                errors.append(
                    "Please write a message before sending."
                )
            else:
                answers.append(answer)

        # Combine all answers into the initial
        # contact request message.
        first_message = "\n\n".join(answers)

        # -----------------------------------------
        # VALIDATE ANSWER LENGTH
        # -----------------------------------------

        if len(first_message) > 2000:

            errors.append(
                "Your answers are too long. "
                "Please keep the combined text under 2000 characters."
            )

        # -----------------------------------------
        # CREATE CONTACT REQUEST
        # -----------------------------------------

        if not errors:

            try:

                with transaction.atomic():

                    # Create a pending request.
                    # Pending = Chat locked.
                    contact_request = ContactRequest.objects.create(
                        post=post,
                        sender=request.user,
                        receiver=post.user,
                        answer=first_message,
                        status="pending"
                    )

                    # Save notification in database.
                    notify(
                        post.user,
                        f'{request.user.username} sent a chat request '
                        f'for "{post.caption}".',
                        post
                    )

                    # ---------------------------------
                    # SOCKET.IO: NOTIFY POST OWNER
                    # ---------------------------------

                    # Capture values before the callback.
                    request_id = contact_request.pk
                    sender_name = request.user.username
                    post_caption = post.caption
                    receiver_id = post.user_id

                    def send_created_event():

                        emit_from_django(
                            "contact_request_created",
                            {
                                "conversation_id": request_id,
                                "sender": sender_name,
                                "post_caption": post_caption,
                                "status": "pending",
                            },
                            receiver_id
                        )

                    # Emit only after a successful commit.
                    transaction.on_commit(
                        send_created_event
                    )

            except IntegrityError:

                # If another request was created at
                # the same time, open that conversation.
                existing = ContactRequest.objects.filter(
                    post=post,
                    sender=request.user
                ).first()

                if existing:
                    return redirect_to_inbox_chat(
                        existing.pk
                    )

                raise

            messages.success(
                request,
                "Your contact request was sent. "
                "Messaging will unlock after the "
                "post owner accepts."
            )

            # ---------------------------------
            # IMPORTANT REDIRECT FIX
            # ---------------------------------

            # User A goes directly to main Inbox
            # with User B's pending chat selected.
            return redirect_to_inbox_chat(
                contact_request.pk
            )

        # Display any validation errors.
        for error in errors:
            messages.error(request, error)

    # Display verification form.
    return render(
        request,
        "verification/contact.html",
        {
            "post": post,
            "questions": questions,
        }
    )


# =========================================
# CONTACT REQUEST LIST
# =========================================

@login_required
def requests_list(request):

    received = (
        ContactRequest.objects
        .filter(receiver=request.user)
        .select_related("post", "sender")
        .order_by("-created_at")
    )

    sent = (
        ContactRequest.objects
        .filter(sender=request.user)
        .select_related("post", "receiver")
        .order_by("-created_at")
    )

    return render(
        request,
        "verification/requests.html",
        {
            "received": received,
            "sent": sent,
        }
    )


# =========================================
# APPROVE OR REJECT CONTACT REQUEST
# =========================================

@login_required
@require_POST
def decide(request, pk):

    decision = request.POST.get("decision")

    if decision not in ("approved", "rejected"):
        raise Http404()

    with transaction.atomic():

        # Lock the request during the decision.
        obj = get_object_or_404(
            ContactRequest.objects
            .select_for_update()
            .select_related("post"),
            pk=pk,
            receiver=request.user
        )

        # ---------------------------------
        # ALREADY REVIEWED
        # ---------------------------------

        if obj.status != "pending":

            messages.warning(
                request,
                "This request has already been reviewed."
            )

            return redirect_to_inbox_chat(
                obj.pk
            )

        # ---------------------------------
        # CLOSED POST VALIDATION
        # ---------------------------------

        if (
            decision == "approved"
            and obj.post.status != "open"
        ):

            messages.error(
                request,
                "Closed posts cannot accept new conversations."
            )

            return redirect_to_inbox_chat(
                obj.pk
            )

        # ---------------------------------
        # SAVE DECISION
        # ---------------------------------

        obj.status = decision
        obj.save(update_fields=["status"])

        # Persistent notification for User A.
        notify(
            obj.sender,
            f'Your contact request for "{obj.post.caption}" '
            f"was {decision}.",
            obj.post
        )

        # ---------------------------------
        # SOCKET.IO STATUS UPDATE
        # ---------------------------------

        conversation_id = obj.pk
        sender_id = obj.sender_id
        receiver_id = obj.receiver_id

        def send_status_update():

            payload = {
                "conversation_id": conversation_id,
                "status": decision,
            }

            # Notify User A.
            emit_from_django(
                "contact_request_updated",
                payload,
                sender_id
            )

            # Notify User B.
            emit_from_django(
                "contact_request_updated",
                payload,
                receiver_id
            )

        transaction.on_commit(
            send_status_update
        )

    messages.success(
        request,
        f"Contact request {decision}."
    )

    # Stay in main Inbox, not separate conversation page.
    return redirect_to_inbox_chat(
        obj.pk
    )
