from django.urls import path
from . import views

app_name = 'client_view'

urlpatterns = [
    path('', views.home, name = 'home'),
    path('about/', views.about, name = 'about'),
    path('contact/', views.contact, name = 'contact'),
    path('thankyou-contact/', views.thankyou_contact, name = 'thankyou_contact'),
    path('coaches/', views.coaches, name = 'coaches'),
    path('used_vehicle/', views.used_vehicle, name = 'used_vehicle'),
    path('services/', views.services, name = 'services'),
    path('api/chat/', views.public_chat, name='public_chat'),
    # Vehicle detail page — /coaches/<slug>/
    path('coaches/<slug:slug>/', views.vehicle_detail, name='vehicle_detail'),
    # Public blog
    path('blog/', views.article_list, name='article_list'),
    path('blog/<int:year>/<int:month>/<slug:slug>/', views.article_detail, name='article_detail'),
]
