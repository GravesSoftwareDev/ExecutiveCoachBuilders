from django.urls import path
from . import views

app_name = 'edit_site'

urlpatterns = [
    path('', views.site_changes, name='site_changes'),
]
