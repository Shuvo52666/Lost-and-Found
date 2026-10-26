
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from communities.models import Community, Membership

from .forms import SignupForm, ProfilePictureForm


# ==========================================
# USER PROFILE
# ==========================================

@login_required
def profile(request):
    user = request.user

    if request.method == "POST":
        form = ProfilePictureForm(
            request.POST,
            request.FILES,
            instance=user
        )

        if form.is_valid():

            # Save the new profile picture.
            old_picture = user.profile_picture.name

            form.save()

            # Remove the previous image from storage
            # after the new image has been saved.
            new_picture = user.profile_picture.name

            if (
                old_picture
                and old_picture != new_picture
            ):
                storage = user.profile_picture.storage

                if storage.exists(old_picture):
                    storage.delete(old_picture)

            messages.success(
                request,
                "Profile picture updated successfully."
            )

            return redirect("profile")

    else:
        form = ProfilePictureForm(instance=user)

    # Count managed communities.
    managed_count = Community.objects.filter(
        admin=user
    ).count()

    # Count joined communities.
    joined_count = (
        Membership.objects
        .filter(user=user)
        .exclude(community__admin=user)
        .values("community_id")
        .distinct()
        .count()
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "managed_count": managed_count,
            "joined_count": joined_count,
        }
    )


# ==========================================
# REMOVE PROFILE PICTURE
# ==========================================

@login_required
@require_POST
def remove_profile_picture(request):
    user = request.user

    # Check whether the user has a picture.
    if not user.profile_picture:
        messages.info(
            request,
            "You do not have a profile picture to remove."
        )
        return redirect("profile")

    # Delete image from media storage and clear
    # the profile_picture database field.
    user.profile_picture.delete(save=True)

    messages.success(
        request,
        "Profile picture removed successfully."
    )

    return redirect("profile")


# ==========================================
# USER REGISTRATION
# ==========================================

def signup(request):
    if request.user.is_authenticated:
        return redirect("feed")

    form = SignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()

        login(request, user)

        messages.success(
            request,
            "Welcome! Your account is ready."
        )

        return redirect("community_list")

    return render(
        request,
        "accounts/signup.html",
        {
            "form": form
        }
    )
