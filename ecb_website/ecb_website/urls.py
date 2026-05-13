"""
URL configuration for ecb_website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('portal/', include('account.urls')),
    path('portal/', include('leads.urls')),
    # Fleet management lives under /portal/fleet/ and requires staff login
    path('portal/fleet/', include('garage.urls')),
    path('portal/site/', include('edit_site.urls')),
    path('portal/blog/', include('blog.urls')),
    path('portal/team/', include('edit_site.team_urls')),
    path('', include('client_view.urls')),
]

# Serve uploaded media files (gunicorn handles this fine for a small/demo site)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
