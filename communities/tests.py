from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from .models import Community,Membership
class CommunitiesTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='alice',email='a@example.com',password='testpassword123!')
        self.client.force_login(self.user)
    def test_create_community_adds_admin(self):
        self.client.post(reverse('community_create'),{'name':'Campus','description':'Local'})
        c=Community.objects.get(name='Campus')
        self.assertTrue(Membership.objects.filter(user=self.user,community=c,role='admin').exists())
    def test_unjoined_user_cannot_view(self):
        other=User.objects.create_user(username='bob',email='b@example.com',password='testpassword123!')
        c=Community.objects.create(name='Private',admin=other)
        self.assertEqual(self.client.get(reverse('community_detail',args=[c.pk])).status_code,404)
