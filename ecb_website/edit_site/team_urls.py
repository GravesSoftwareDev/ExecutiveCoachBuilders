from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    path('', views.team_member_list, name='team_member_list'),
    path('add/', views.team_member_add, name='team_member_add'),
    path('<int:pk>/edit/', views.team_member_edit, name='team_member_edit'),
    path('<int:pk>/delete/', views.team_member_delete, name='team_member_delete'),
]
