from django import forms
from .models import VerificationQuestion,ContactRequest
class QuestionForm(forms.ModelForm):
    class Meta:
        model=VerificationQuestion
        fields=['question']
class ContactForm(forms.ModelForm):
    class Meta:
        model=ContactRequest
        fields=['answer']
        labels={'answer':'Answers / ownership evidence (only shown to the post author)'}
        widgets={'answer':forms.Textarea(attrs={'rows':5})}
