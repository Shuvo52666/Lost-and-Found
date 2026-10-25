from django.urls import path
from . import views
urlpatterns=[
 path('',views.feed,name='feed'),
 path('create/',views.create,name='post_create'),
 path('<int:pk>/',views.detail,name='post_detail'),
 path('<int:pk>/comment/',views.comment,name='post_comment'),
 path('<int:pk>/report/',views.report,name='post_report'),
 path('<int:pk>/status/',views.status,name='post_status'),
 
path(
    "posts/<int:post_id>/report/",
    views.report_post,
    name="report_post"
),

path(
    "communities/<int:community_id>/manage-posts/",
    views.manage_community_posts,
    name="manage_community_posts"
),

path(
    "posts/<int:post_id>/moderate/",
    views.moderate_post,
    name="moderate_post"
),

path(
    "posts/<int:post_id>/admin-delete/",
    views.admin_delete_post,
    name="admin_delete_post"
),

]
