
from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    signup,
    profile,
    remove_profile_picture
)

urlpatterns = [

    # USER REGISTRATION
    path(
        "signup/",
        signup,
        name="signup"
    ),

    # USER LOGIN
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html"
        ),
        name="login"
    ),

    # USER LOGOUT
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout"
    ),

    # USER PROFILE
    path(
        "profile/",
        profile,
        name="profile"
    ),

    # REMOVE PROFILE PICTURE
    path(
        "profile/remove-photo/",
        remove_profile_picture,
        name="remove_profile_picture"
    ),

]
