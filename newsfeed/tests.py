from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from communities.models import Community,Membership
from .models import Post
class PostsTests(TestCase):
    def setUp(self):
        self.a=User.objects.create_user('alice','a@example.com','secretpass123')
        self.b=User.objects.create_user('bob','b@example.com','secretpass123')
        self.c=Community.objects.create(name='Test',admin=self.a)
        Membership.objects.create(user=self.a,community=self.c)
        self.p=Post.objects.create(user=self.a,community=self.c,type='found',caption='Keys',description='Set of keys')
    def test_feed_is_private_to_members(self):
        self.client.force_login(self.b)
        self.assertNotContains(self.client.get(reverse('feed')),'Keys')
        self.assertEqual(self.client.get(reverse('post_detail',args=[self.p.pk])).status_code,404)
    def test_cannot_post_to_unjoined_community(self):
        self.client.force_login(self.b)
        self.client.post(reverse('post_create'),{'community':self.c.pk,'type':'lost','caption':'Bag','description':'Blue bag'})
        self.assertFalse(Post.objects.filter(caption='Bag').exists())
