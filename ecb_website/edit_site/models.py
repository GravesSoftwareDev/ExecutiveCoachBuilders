from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings as Settings

# Create your models here.
class SiteSettings(models.Model):
    name = models.CharField(max_length=100, default="_")
    value = models.CharField(max_length=255, default="_")
    type = models.CharField(max_length=5, choices={"T":"TEXT", "V":"VIDEO", "I":"IMAGE"}, default="T")

    def media_type(this):
        return this.type == 'I' or this.type == 'V'

    def get_value(this):
        if this.media_type():
            return Settings.MEDIA_URL + this.value
        return this.value
    
    class Meta:
        ordering = ["name"]