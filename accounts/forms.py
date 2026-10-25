
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from PIL import Image

from .models import User


# =========================================
# USER REGISTRATION FORM
# =========================================

class SignupForm(UserCreationForm):

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )


# =========================================
# PROFILE PICTURE FORM
# =========================================

class ProfilePictureForm(forms.ModelForm):

    class Meta:
        model = User

        fields = ["profile_picture"]

        widgets = {
            "profile_picture": forms.ClearableFileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp",
                    "id": "profile-picture-input",
                }
            )
        }

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")

        if not picture:
            return picture

        # Maximum image size: 5 MB
        if picture.size > 5 * 1024 * 1024:
            raise ValidationError(
                "Profile picture must be 5 MB or smaller."
            )

        # Only allow supported image formats
        if getattr(picture, "content_type", "") not in (
            "image/jpeg",
            "image/png",
            "image/webp",
        ):
            raise ValidationError(
                "Please upload a JPG, PNG, or WebP image."
            )

        # Verify the actual uploaded image
        try:
            picture.seek(0)

            with Image.open(picture) as image:
                image.verify()

            picture.seek(0)

        except Exception:
            raise ValidationError(
                "The uploaded file is not a valid image."
            )

        return picture
