from django.urls import path
from . import views

app_name = 'edit_site'

urlpatterns = [
    path('', views.site_changes, name='site_changes'),
    path('site_changes/<name>', views.site_changes, name='site_changes'),
    path('admin_view/', views.admin_view, name='admin_view'),
]
