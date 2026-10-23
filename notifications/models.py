from django.conf import settings
from django.db import models
class Notification(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='notifications')
    message=models.CharField(max_length=500)
    post=models.ForeignKey('newsfeed.Post',null=True,blank=True,on_delete=models.SET_NULL)
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']
