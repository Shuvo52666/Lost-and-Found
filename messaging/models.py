from django.conf import settings
from django.db import models
class Message(models.Model):
    request=models.ForeignKey('verification.ContactRequest',on_delete=models.CASCADE,related_name='messages')
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='messages_sent')
    receiver=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='messages_received')
    content=models.TextField(max_length=3000)
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['created_at']
