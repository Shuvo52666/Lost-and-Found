

from django.db import transaction
from .models import Notification


def notify(user, message, post=None, contact_request=None):

    notification = Notification.objects.create(
        user=user,
        message=message,
        post=post,
        contact_request=contact_request
    )

    def send_realtime():
        from config.socketio import emit_from_django

        unread_count = Notification.objects.filter(
            user_id=user.pk,
            is_read=False
        ).count()

        emit_from_django(
            "new_notification",
            {
                "id": notification.pk,
                "message": notification.message,
                "unread_count": unread_count,
                "post_id": notification.post_id,
                "contact_request_id": notification.contact_request_id,
                "created_at": notification.created_at.isoformat(),
            },
            user.pk
        )

    transaction.on_commit(send_realtime)

    return notification