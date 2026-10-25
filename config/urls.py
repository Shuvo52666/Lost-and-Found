from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import reverse

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("feed")

    return redirect("login")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home_redirect, name="home"),
    path('accounts/', include('accounts.urls')),
    path('communities/', include('communities.urls')),
    path('feed/', include('newsfeed.urls')),
    path('verification/', include('verification.urls')),
    path('inbox/', include('messaging.urls')),
    path('notifications/', include('notifications.urls')),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
