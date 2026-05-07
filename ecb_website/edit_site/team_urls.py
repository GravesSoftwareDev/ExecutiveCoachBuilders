from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    path('', views.team_member_list, name='team_member_list'),
    path('add/', views.team_member_add, name='team_member_add'),
    path('<int:pk>/edit/', views.team_member_edit, name='team_member_edit'),
    path('<int:pk>/delete/', views.team_member_delete, name='team_member_delete'),
    path('users/', views.portal_user_list, name='portal_user_list'),
    path('users/add/', views.portal_user_add, name='portal_user_add'),
    path('users/<int:pk>/edit/', views.portal_user_edit, name='portal_user_edit'),
    path('users/<int:pk>/delete/', views.portal_user_delete, name='portal_user_delete'),
]
