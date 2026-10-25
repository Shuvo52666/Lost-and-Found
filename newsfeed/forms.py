
from django import forms
from django.db.models import Q

from .models import Post, Comment, Report
from communities.models import Community


# ==========================================
# CREATE LOST / FOUND POST FORM
# ==========================================

class PostForm(forms.ModelForm):

    class Meta:
        model = Post

        fields = [
            "community",
            "type",
            "caption",
            "description",
            "image",
        ]

        widgets = {
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Add more details about your item (optional)",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Description is optional
        self.fields["description"].required = False

        # Image upload remains optional if defined
        # with blank=True in the Post model.

        if user is not None:

            # Allow communities the user joined
            # or manages as an admin.
            self.fields["community"].queryset = (
                Community.objects.filter(
                    Q(memberships__user=user) |
                    Q(admin=user)
                )
                .distinct()
                .order_by("name")
            )


# ==========================================
# COMMENT FORM
# ==========================================

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ["content"]


# ==========================================
# REPORT FORM
# ==========================================

class ReportForm(forms.ModelForm):

    class Meta:
        model = Report
        fields = [
            "reason",
            "description",
        ]
