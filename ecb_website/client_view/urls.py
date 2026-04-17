from django.urls import path
from . import views

app_name = 'client_view'

urlpatterns = [
    path('', views.home, name='home'),
    # Vehicle detail page — /coaches/<slug>/
    path('coaches/<slug:slug>/', views.vehicle_detail, name='vehicle_detail'),
]
