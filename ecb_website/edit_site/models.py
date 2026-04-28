from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings as Settings

# Create your models here.
class SiteSetting(models.Model):
    name = models.CharField(max_length=100, default="_", blank=True)
    file_value = models.FileField(upload_to='site_settings/', default="_")
    text_value = models.CharField(max_length=255, default="_", blank=True)
    file = models.BooleanField(default="0")

    def get_value(this):
        if this.file:
            return this.file_value.url
        return this.text_value
    
    class Meta:
        ordering = ["name"]