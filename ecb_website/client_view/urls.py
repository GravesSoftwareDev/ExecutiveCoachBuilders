from django.urls import path
from . import views

app_name = 'client_view'

urlpatterns = [
    path('', views.home, name = 'home'),
]
