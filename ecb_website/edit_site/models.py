from django.db import models
from django.core.validators import FileExtensionValidator

# Create your models here.
class SiteSettings(models.Model):
    primaryCenterVideo = models.FileField(upload_to='site_settings/', null=False, validators=[FileExtensionValidator(allowed_extensions=['MOV','avi','mp4','webm','mkv'])])
