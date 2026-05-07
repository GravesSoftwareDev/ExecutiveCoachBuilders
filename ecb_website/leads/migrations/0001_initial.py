import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(blank=True, max_length=25, validators=[django.core.validators.RegexValidator(message='Please enter a valid phone number.', regex='^\\+?\\(?\\d{1,4}\\)?[\\s\\-\\.\\d]{5,20}$')])),
                ('company', models.CharField(blank=True, max_length=255, null=True)),
                ('budget', models.IntegerField(blank=True, null=True)),
                ('interest', models.CharField(choices=[('BUS', 'Bus'), ('COACH', 'Coach'), ('SPRINTER', 'Sprinter Van'), ('CUSTOM', 'Custom')], default='CUSTOM', max_length=20)),
                ('passenger_count', models.CharField(blank=True, default='', max_length=60)),
                ('timeline', models.CharField(blank=True, default='', max_length=120)),
                ('use_case', models.CharField(blank=True, default='', max_length=160)),
                ('source', models.CharField(blank=True, default='', max_length=80)),
                ('source_url', models.CharField(blank=True, default='', max_length=255)),
                ('message', models.TextField(blank=True, default='')),
                ('pipeline_stage', models.CharField(choices=[('new', 'New'), ('in_progress', 'In progress'), ('closed', 'Closed')], default='new', max_length=32)),
                ('priority', models.CharField(choices=[('normal', 'Normal'), ('high', 'High')], default='normal', max_length=16)),
                ('is_hot', models.BooleanField(default=False)),
                ('hot_reason', models.TextField(blank=True, default='')),
                ('ai_structured', models.JSONField(blank=True, default=dict)),
                ('ai_structured_updated_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_leads', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='LeadChatSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, default='', max_length=200)),
                ('is_archived', models.BooleanField(default=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('last_activity_at', models.DateTimeField(auto_now=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_sessions', to='leads.lead')),
                ('started_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chat_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_activity_at'],
                'indexes': [models.Index(fields=['lead', '-last_activity_at'], name='leads_leadc_lead_id_f3a982_idx')],
            },
        ),
        migrations.CreateModel(
            name='LeadMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(choices=[('in', 'Inbound'), ('out', 'Outbound'), ('internal', 'Internal')], max_length=16)),
                ('channel', models.CharField(choices=[('form', 'Website form'), ('email', 'Email'), ('note', 'Note'), ('system', 'System'), ('chat', 'Assistant chat')], max_length=16)),
                ('status', models.CharField(choices=[('received', 'Received'), ('draft', 'Draft'), ('sent', 'Sent'), ('logged', 'Logged')], max_length=16)),
                ('subject', models.CharField(blank=True, default='', max_length=998)),
                ('body', models.TextField(blank=True, default='')),
                ('message_id', models.CharField(blank=True, default='', max_length=998)),
                ('in_reply_to', models.CharField(blank=True, default='', max_length=998)),
                ('from_email', models.EmailField(blank=True, default='', max_length=254)),
                ('to_email', models.EmailField(blank=True, default='', max_length=254)),
                ('is_ai_generated', models.BooleanField(default=False)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, help_text='Employee who created or sent this message, if any.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lead_messages', to=settings.AUTH_USER_MODEL)),
                ('chat_session', models.ForeignKey(blank=True, help_text='Set only for channel=chat messages.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='leads.leadchatsession')),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='leads.lead')),
            ],
            options={
                'ordering': ['created_at'],
                'indexes': [
                    models.Index(fields=['lead', 'created_at'], name='leads_leadm_lead_id_4f1a4d_idx'),
                    models.Index(fields=['direction', 'channel'], name='leads_leadm_directi_0a637a_idx'),
                    models.Index(fields=['chat_session', 'created_at'], name='leads_leadm_chat_se_ef200f_idx'),
                    models.Index(fields=['message_id'], name='leads_leadm_message_119988_idx'),
                    models.Index(fields=['in_reply_to'], name='leads_leadm_in_repl_794ca6_idx'),
                ],
            },
        ),
    ]
