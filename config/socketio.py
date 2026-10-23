
import asyncio
import logging
from http.cookies import SimpleCookie

import socketio
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user
from django.contrib.sessions.backends.db import SessionStore
from django.db import transaction
from django.http import HttpRequest

from messaging.models import Message
from verification.models import ContactRequest


logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=None,
    logger=settings.DEBUG,
    engineio_logger=settings.DEBUG,
)

# The running ASGI server's event loop.
socket_loop = None


def emit_from_django(event, data, user_id):
    """
    Called by synchronous Django views/services.
    Safe for a single Uvicorn worker.
    """
    loop = socket_loop

    if loop is None or not loop.is_running():
        logger.warning(
            "Socket.IO event skipped: server loop unavailable."
        )
        return

    future = asyncio.run_coroutine_threadsafe(
        sio.emit(
            event,
            data,
            room=f"user_{user_id}"
        ),
        loop
    )

    def check_result(result):
        try:
            result.result()
        except Exception:
            logger.exception("Socket.IO emission failed.")

    future.add_done_callback(check_result)


def authenticate_socket(environ):
    """
    Authenticate the browser using its Django session.
    Uses the default database session backend.
    """
    raw_cookie = environ.get("HTTP_COOKIE", "")

    cookies = SimpleCookie()

    try:
        cookies.load(raw_cookie)
    except Exception:
        return None

    session_cookie = cookies.get(
        settings.SESSION_COOKIE_NAME
    )

    if not session_cookie:
        return None

    session = SessionStore(
        session_key=session_cookie.value
    )

    request = HttpRequest()
    request.session = session

    user = get_user(request)

    if not user.is_authenticated or not user.is_active:
        return None

    return user.pk


def save_socket_message(user_id, request_id, content):
    """
    Validate access and persist a message.
    """
    with transaction.atomic():

        conversation = (
            ContactRequest.objects
            .select_for_update()
            .select_related("sender", "receiver", "post")
            .filter(pk=request_id)
            .first()
        )

        if conversation is None:
            return {"error": "Conversation not found."}

        if user_id not in (
            conversation.sender_id,
            conversation.receiver_id
        ):
            return {"error": "Access denied."}

        if conversation.status != "approved":
            return {"error": "This chat is locked."}

        sender = (
            conversation.sender
            if user_id == conversation.sender_id
            else conversation.receiver
        )

        receiver = (
            conversation.receiver
            if user_id == conversation.sender_id
            else conversation.sender
        )

        message = Message.objects.create(
            request=conversation,
            sender=sender,
            receiver=receiver,
            content=content
        )

        return {
            "id": message.pk,
            "conversation_id": conversation.pk,
            "sender_id": sender.pk,
            "sender": sender.username,
            "receiver_id": receiver.pk,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "post_id": conversation.post_id,
            "post_caption": conversation.post.caption,
        }


@sio.event
async def connect(sid, environ, auth):
    global socket_loop

    user_id = await sync_to_async(
        authenticate_socket,
        thread_sensitive=True
    )(environ)

    if user_id is None:
        logger.warning("Socket.IO rejected an unauthenticated client.")
        raise socketio.exceptions.ConnectionRefusedError(
            "Authentication required."
        )

    socket_loop = asyncio.get_running_loop()

    await sio.save_session(
        sid,
        {"user_id": user_id}
    )

    await sio.enter_room(
        sid,
        f"user_{user_id}"
    )

    logger.info("Socket.IO connected user %s", user_id)


@sio.event
async def disconnect(sid, reason=None):
    logger.info("Socket.IO disconnected: %s", sid)


@sio.on("send_message")
async def send_message(sid, data):

    session = await sio.get_session(sid)
    user_id = session["user_id"]

    if not isinstance(data, dict):
        return {"error": "Invalid message data."}

    try:
        request_id = int(data.get("conversation_id"))
        content = data.get("content", "")

        if not isinstance(content, str):
            return {"error": "Invalid message content."}

        content = content.strip()

    except (TypeError, ValueError):
        return {"error": "Invalid conversation ID."}

    if not content or len(content) > 3000:
        return {
            "error": "Message must be 1-3000 characters."
        }

    result = await sync_to_async(
        save_socket_message,
        thread_sensitive=True
    )(user_id, request_id, content)

    if "error" in result:
        return result

    payload = {
        "id": result["id"],
        "conversation_id": result["conversation_id"],
        "sender_id": result["sender_id"],
        "sender": result["sender"],
        "content": result["content"],
        "created_at": result["created_at"],
    }

    # Emit from the running Socket.IO event loop.
    await sio.emit(
        "new_message",
        payload,
        room=f"user_{result['sender_id']}"
    )

    await sio.emit(
        "new_message",
        payload,
        room=f"user_{result['receiver_id']}"
    )

    # Save a persistent notification.
    from notifications.services import notify
    from django.contrib.auth import get_user_model
    from newsfeed.models import Post

    def create_message_notification():
        receiver = get_user_model().objects.get(
            pk=result["receiver_id"]
        )

        post = Post.objects.get(
            pk=result["post_id"]
        )

        notify(
            receiver,
            f'New message from {result["sender"]} '
            f'about "{result["post_caption"]}".',
            post
        )

    try:
        await sync_to_async(
            create_message_notification,
            thread_sensitive=True
        )()
    except Exception:
        logger.exception(
            "Message saved, but notification creation failed."
        )

    return {
        "success": True,
        "id": result["id"]
    }
