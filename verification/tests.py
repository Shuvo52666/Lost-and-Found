from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from communities.models import Community,Membership
from newsfeed.models import Post
from .models import ContactRequest
class VerificationTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user('owner','owner@example.com','secretpass123')
        self.claimant=User.objects.create_user('claimant','claimant@example.com','secretpass123')
        self.c=Community.objects.create(name='Campus',admin=self.owner)
        Membership.objects.create(user=self.owner,community=self.c)
        Membership.objects.create(user=self.claimant,community=self.c)
        self.post=Post.objects.create(user=self.owner,community=self.c,type='found',caption='Wallet',description='Black')
    def test_request_must_be_approved_before_chat(self):
        self.client.force_login(self.claimant)
        self.client.post(reverse('contact_request',args=[self.post.pk]),{'answer':'I can describe it'})
        r=ContactRequest.objects.get(post=self.post,sender=self.claimant)
        self.assertEqual(self.client.get(reverse('conversation',args=[r.pk])).status_code,404)
        self.client.force_login(self.owner)
        self.client.post(reverse('request_decide',args=[r.pk]),{'decision':'approved'})
        self.client.force_login(self.claimant)
        self.assertEqual(self.client.get(reverse('conversation',args=[r.pk])).status_code,200)
    def test_third_party_cannot_read_conversation(self):
        outsider=User.objects.create_user('outsider','o@example.com','secretpass123')
        r=ContactRequest.objects.create(post=self.post,sender=self.claimant,receiver=self.owner,status='approved')
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(reverse('conversation',args=[r.pk])).status_code,404)
