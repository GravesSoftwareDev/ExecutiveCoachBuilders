from django.urls import path
from . import views

app_name = 'client_view'

urlpatterns = [
    path('', views.home, name = 'home'),
    path('about/', views.about, name = 'about'),
    path('contact/', views.contact, name = 'contact'),
    path('thankyou-contact/', views.thankyou_contact, name = 'thankyou_contact'),
    path('coaches/', views.coaches, name = 'coaches'),
    path('services/', views.services, name = 'services'),
    # Vehicle detail page — /coaches/<slug>/
    path('coaches/<slug:slug>/', views.vehicle_detail, name='vehicle_detail'),
]
