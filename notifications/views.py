from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.views.decorators.http import require_POST
from .models import Notification
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

from messaging.models import Message
from verification.models import ContactRequest

@login_required
def list_notifications(request):
    return render(request,'notifications/list.html',{'notifications':Notification.objects.filter(user=request.user)})


@login_required
@require_POST
def mark_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    messages.success(
        request,
        "All notifications marked as read."
    )

    return redirect("inbox")




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

    return JsonResponse({
        "unread_messages": unread_messages,
        "pending_requests": pending_requests,
        "unread_notifications": unread_notifications,
        "inbox_badge_count": (
            unread_messages + pending_requests
        ),
    })


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

from messaging.models import Message
from verification.models import ContactRequest


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

    return JsonResponse({
        "unread_messages": unread_messages,
        "pending_requests": pending_requests,
        "inbox_badge_count": (
            unread_messages + pending_requests
        ),
    })

