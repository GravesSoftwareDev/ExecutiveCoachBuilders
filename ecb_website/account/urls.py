from django.contrib.auth import views as auth_views
from django.urls import path

from . import settings_views, views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('settings/', settings_views.agent_settings_view, name='settings'),
    path('', views.dashboard, name='dashboard'),
]
