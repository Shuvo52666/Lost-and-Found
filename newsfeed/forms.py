from django import forms
from .models import Post, Comment, Report
class PostForm(forms.ModelForm):
    class Meta:
        model=Post
        fields=['community','type','caption','description','image']
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        if user is not None:
            from communities.models import Community
            self.fields['community'].queryset=Community.objects.filter(memberships__user=user).distinct()
class CommentForm(forms.ModelForm):
    class Meta:
        model=Comment
        fields=['content']
class ReportForm(forms.ModelForm):
    class Meta:
        model=Report
        fields=['reason','description']
