from django.test import TestCase
from django.urls import reverse
from .models import User
class AuthenticationTests(TestCase):
    def test_signup(self):
        result=self.client.post(reverse('signup'),{'username':'alice','email':'alice@example.com','password1':'StrongerTestPass_914!','password2':'StrongerTestPass_914!'})
        self.assertEqual(result.status_code,302)
        self.assertTrue(User.objects.filter(username='alice').exists())
