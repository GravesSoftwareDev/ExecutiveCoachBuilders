from django.db import migrations, models
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_employee_can_edit_blog_employee_can_edit_fleet_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='message',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='lead',
            name='budget',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='lead',
            name='company',
            field=models.CharField(blank=True, default=None, max_length=150, null=True),
        ),
        migrations.AlterModelOptions(
            name='lead',
            options={'ordering': ['-created_at']},
        ),
    ]
