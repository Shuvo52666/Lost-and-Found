from django.urls import path
from . import views
urlpatterns=[
 path('',views.feed,name='feed'),
 path('create/',views.create,name='post_create'),
 path('<int:pk>/',views.detail,name='post_detail'),
 path('<int:pk>/comment/',views.comment,name='post_comment'),
 path('<int:pk>/report/',views.report,name='post_report'),
 path('<int:pk>/status/',views.status,name='post_status'),
]
