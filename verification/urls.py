from django.urls import path
from . import views
urlpatterns=[
 path('requests/',views.requests_list,name='requests_list'),
 path('posts/<int:pk>/question/',views.add_question,name='question_add'),
 path('posts/<int:pk>/contact/',views.contact,name='contact_request'),
 path('requests/<int:pk>/decide/',views.decide,name='request_decide'),
]
