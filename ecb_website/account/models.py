from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Regex Validators
phone_regex = RegexValidator(
    regex=r'^\+?\(?\d{1,4}\)?[\s\-\.\d]{5,20}$',
    message='Please enter a valid phone number.'
)

# Create your models here.

class Employee(AbstractUser):

    class Role(models.TextChoices):
        agent = 'AGENT','Agent'
        admin = 'ADMIN','Admin'
    
    role = models.CharField(
        choices=Role.choices,
        default=Role.agent
    )

class Lead(models.Model):
    class Interest(models.TextChoices):
        bus = 'BUS','Bus'
        coach = 'COACH','Coach'
        sprinter = 'SPRINTER','Sprinter Van'
        custom = 'CUSTOM','Custom'
    budget = models.IntegerField()
    phone_number = models.CharField(validators=[phone_regex], max_length=25, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    company = models.CharField(blank=True, null=True, default=None)
    interest = models.CharField(
        choices = Interest.choices,
        default=Interest.custom
    )
    