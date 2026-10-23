from django.urls import path
from . import views
urlpatterns=[
    path('',views.inbox,name='inbox'),path('<int:pk>/',views.conversation,name='conversation'),
    path('<int:pk>/send/',views.send,name='send_message'),
    path(
    "<int:pk>/mark-read/",
    views.mark_conversation_read,
    name="conversation_mark_read"
),
]
