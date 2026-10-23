
from messaging.models import Message
from verification.models import ContactRequest
from notifications.models import Notification


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {
            "unread_notification_count": 0,
            "unread_message_count": 0,
            "pending_request_count": 0,
            "inbox_badge_count": 0,
        }

    user = request.user

    unread_messages = Message.objects.filter(
        receiver=user,
        is_read=False
    ).count()

    pending_requests = ContactRequest.objects.filter(
        receiver=user,
        status="pending"
    ).count()

    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()

    return {
        "unread_notification_count": unread_notifications,
        "unread_message_count": unread_messages,
        "pending_request_count": pending_requests,
        "inbox_badge_count": (
            unread_messages + pending_requests
        ),
    }
