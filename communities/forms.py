from django import forms
from .models import Community
class CommunityForm(forms.ModelForm):
    class Meta:
        model=Community
        fields=['name','description']
class JoinForm(forms.Form):
    code = forms.CharField(label='Community ID', max_length=20)
