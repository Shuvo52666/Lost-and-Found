
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from newsfeed.views import accessible_post
from notifications.services import notify
from config.socketio import emit_from_django

from .models import ContactRequest
from .forms import QuestionForm


# =========================================
# ADD VERIFICATION QUESTION
# =========================================

@login_required
def add_question(request, pk):

    post = accessible_post(request.user, pk)

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
            "submit_label": "Add question"
        }
    )


# =========================================
# SEND CONTACT REQUEST
# =========================================

@login_required
def contact(request, pk):

    post = accessible_post(request.user, pk)

    # Users cannot contact themselves or use closed posts.
    if post.user_id == request.user.id or post.status != "open":
        raise Http404()

    # Prevent duplicate requests for the same post.
    previous = ContactRequest.objects.filter(
        post=post,
        sender=request.user
    ).first()

    if previous:
        return redirect("conversation", pk=previous.pk)

    questions = list(
        post.verification_questions.order_by("id")
    )

    if request.method == "POST":

        answers = []
        errors = []

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

            answer = request.POST.get(
                "message", ""
            ).strip()

            if not answer:
                errors.append(
                    "Please write a message before sending."
                )
            else:
                answers.append(answer)

        first_message = "\n\n".join(answers)

        if len(first_message) > 2000:
            errors.append(
                "Your answers are too long. "
                "Please keep the combined text under 2000 characters."
            )

        if not errors:

            try:
                with transaction.atomic():

                    # Create pending contact request.
                    contact_request = ContactRequest.objects.create(
                        post=post,
                        sender=request.user,
                        receiver=post.user,
                        answer=first_message,
                        status="pending"
                    )

                    # Save a persistent notification.
                    notify(
                        post.user,
                        f'{request.user.username} sent a chat request '
                        f'for "{post.caption}".',
                        post
                    )

                    # Send real-time event after database commit.
                    def send_created_event():

                        emit_from_django(
                            "contact_request_created",
                            {
                                "conversation_id": contact_request.pk,
                                "sender": request.user.username,
                                "post_caption": post.caption,
                                "status": "pending",
                            },
                            post.user_id
                        )

                    transaction.on_commit(send_created_event)

            except IntegrityError:

                existing = ContactRequest.objects.filter(
                    post=post,
                    sender=request.user
                ).first()

                if existing:
                    return redirect(
                        "conversation",
                        pk=existing.pk
                    )

                raise

            messages.success(
                request,
                "Your request was sent. "
                "Messaging will unlock after approval."
            )

            return redirect(
                "conversation",
                pk=contact_request.pk
            )

        for error in errors:
            messages.error(request, error)

    return render(
        request,
        "verification/contact.html",
        {
            "post": post,
            "questions": questions
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
    )

    sent = (
        ContactRequest.objects
        .filter(sender=request.user)
        .select_related("post", "receiver")
    )

    return render(
        request,
        "verification/requests.html",
        {
            "received": received,
            "sent": sent
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

        # Lock the row while checking and updating status.
        obj = get_object_or_404(
            ContactRequest.objects
            .select_for_update()
            .select_related("post"),
            pk=pk,
            receiver=request.user
        )

        if obj.status != "pending":
            messages.warning(
                request,
                "This request has already been reviewed."
            )

            return redirect("conversation", pk=obj.pk)

        # Cannot approve a request for a closed post.
        if decision == "approved" and obj.post.status != "open":

            messages.error(
                request,
                "Closed posts cannot accept new conversations."
            )

            return redirect("conversation", pk=obj.pk)

        # Update request status.
        obj.status = decision
        obj.save(update_fields=["status"])

        # Create persistent notification.
        notify(
            obj.sender,
            f'Your contact request for "{obj.post.caption}" '
            f"was {decision}.",
            obj.post
        )

        # Notify both connected users after commit.
        def send_status_update():

            payload = {
                "conversation_id": obj.pk,
                "status": decision,
            }

            emit_from_django(
                "contact_request_updated",
                payload,
                obj.sender_id
            )

            emit_from_django(
                "contact_request_updated",
                payload,
                obj.receiver_id
            )

        transaction.on_commit(send_status_update)

    messages.success(
        request,
        f"Contact request {decision}."
    )

    return redirect("conversation", pk=obj.pk)
