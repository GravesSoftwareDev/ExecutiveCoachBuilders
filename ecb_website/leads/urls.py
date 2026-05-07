from django.urls import path

from . import views

app_name = 'leads'

urlpatterns = [
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/new/', views.lead_create, name='lead_create'),
    path('leads/api/', views.lead_api_collection, name='lead_api_collection'),
    path('leads/api/<int:pk>/', views.lead_api_detail, name='lead_api_detail'),
    path('leads/<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('leads/<int:pk>/edit/', views.lead_edit, name='lead_edit'),
    path('leads/<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/claim/', views.claim_lead, name='lead_claim'),
    path('leads/<int:pk>/stage/', views.set_stage, name='lead_stage'),
    path('leads/<int:pk>/note/', views.add_note, name='lead_note'),
    path('leads/<int:pk>/email/send/', views.lead_send_email, name='lead_send_email'),
    path('leads/<int:pk>/ask/', views.ask_ai, name='lead_ask'),
    path('leads/<int:pk>/ask/stream/', views.ask_ai_stream, name='lead_ask_stream'),
    path('leads/<int:pk>/chat/panel/', views.chat_panel, name='chat_panel'),
    path('leads/<int:pk>/task', views.task_legacy_redirect, name='lead_task_legacy'),
    path('leads/<int:pk>/chat/new/', views.new_chat, name='chat_new'),
    path('leads/<int:lead_pk>/chat/<int:pk>/resume/', views.resume_chat, name='chat_resume'),
    path(
        'leads/<int:lead_pk>/chat/<int:pk>/delete/',
        views.delete_chat_session,
        name='chat_delete',
    ),
]
