from django.urls import path
from . import views

app_name = 'edit_site'

urlpatterns = [
    path('', views.site_changes, name='site_changes'),
    path('site_changes/<name>', views.site_changes, name='site_changes'),
    path('admin_view/', views.admin_view, name='admin_view'),
    # About page
    path('about/', views.about_edit, name='about_edit'),
    # Services management
    path('services/', views.service_list, name='service_list'),
    path('services/add/', views.service_add, name='service_add'),
    path('services/<int:pk>/edit/', views.service_edit, name='service_edit'),
    path('services/<int:pk>/delete/', views.service_delete, name='service_delete'),
]
