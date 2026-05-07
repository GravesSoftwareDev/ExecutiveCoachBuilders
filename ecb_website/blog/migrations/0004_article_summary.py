from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_article_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='summary',
            field=models.CharField(blank=True, default='', help_text='Short excerpt for the public news list and search previews.', max_length=500),
        ),
        migrations.RemoveField(
            model_name='article',
            name='tags',
        ),
    ]
