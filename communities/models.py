import secrets
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator

def community_code():
    return secrets.token_hex(5).upper()
class Community(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    join_code = models.CharField(max_length=20, unique=True, default=community_code, editable=False)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_communities')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
class Membership(models.Model):
    ROLE_CHOICES = [('admin','Admin'),('member','Member')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','community'], name='one_membership_per_community')]
    def __str__(self): return f'{self.user} — {self.community}'
