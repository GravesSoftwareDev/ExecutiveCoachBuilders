from django.urls import path
from . import views

app_name = 'garage'

urlpatterns = [
    # Fleet management list — /portal/fleet/
    path('', views.vehicle_list, name='vehicle_list'),
    # Add a new vehicle — /portal/fleet/add/
    path('add/', views.vehicle_add, name='vehicle_add'),
    # Edit an existing vehicle — /portal/fleet/<pk>/edit/
    path('<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    # Delete a vehicle — /portal/fleet/<pk>/delete/
    path('<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
]
