
from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.community_list,
        name="community_list"
    ),
    path(
        "create/",
        views.create,
        name="community_create"
    ),
    path(
        "join/",
        views.join,
        name="community_join"
    ),
    path(
        "join/<str:code>/",
        views.join_code,
        name="community_join_code"
    ),
    path(
        "<int:pk>/enter/",
        views.enter_community,
        name="enter_community"
    ),
    path(
        "<int:pk>/",
        views.detail,
        name="community_detail"
    ),
    path(
        "<int:pk>/qr/",
        views.qr,
        name="community_qr"
    ),
]
