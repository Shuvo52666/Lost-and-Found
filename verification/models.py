from django.conf import settings
from django.db import models
class VerificationQuestion(models.Model):
    post=models.ForeignKey('newsfeed.Post',on_delete=models.CASCADE,related_name='verification_questions')
    question=models.CharField(max_length=300)
    def __str__(self): return self.question
class ContactRequest(models.Model):
    STATES=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')]
    post=models.ForeignKey('newsfeed.Post',on_delete=models.CASCADE,related_name='contact_requests')
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='sent_requests')
    receiver=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='received_requests')
    answer=models.TextField(max_length=2000,blank=True)
    status=models.CharField(max_length=12,choices=STATES,default='pending')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['post','sender'],name='one_request_per_sender_post')]
    def __str__(self): return f'{self.sender} → {self.receiver}: {self.status}'
