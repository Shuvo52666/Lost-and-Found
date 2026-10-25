from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from .forms import SignupForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from communities.models import Community, Membership

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from communities.models import Community, Membership
from .forms import ProfilePictureForm


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
            form.save()

            messages.success(
                request,
                "Profile picture updated successfully."
            )

            return redirect("profile")
    else:
        form = ProfilePictureForm(instance=user)

    managed_count = Community.objects.filter(
        admin=user
    ).count()

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
def signup(request):
    if request.user.is_authenticated:
        return redirect('feed')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome! Your account is ready.')
        return redirect('community_list')
    return render(request, 'accounts/signup.html', {'form': form})
