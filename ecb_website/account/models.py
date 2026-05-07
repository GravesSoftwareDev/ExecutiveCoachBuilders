from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings

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

    can_edit_site     = models.BooleanField(default=False)
    can_edit_fleet    = models.BooleanField(default=False)
    can_edit_blog     = models.BooleanField(default=False)
    can_edit_services = models.BooleanField(default=False)
    can_edit_team     = models.BooleanField(default=False)

    @property
    def is_portal_admin(self):
        return self.role == self.Role.admin or self.is_superuser

class Lead(models.Model):
    class Interest(models.TextChoices):
        bus = 'BUS','Bus'
        coach = 'COACH','Coach'
        sprinter = 'SPRINTER','Sprinter Van'
        custom = 'CUSTOM','Custom'
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(validators=[phone_regex], max_length=25, blank=True)
    company = models.CharField(max_length=150, blank=True, null=True, default=None)
    interest = models.CharField(
        choices=Interest.choices,
        default=Interest.custom
    )
    budget = models.PositiveIntegerField(blank=True, null=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Status(models.TextChoices):
        new          = 'NEW',          'New'
        active       = 'ACTIVE',       'Actively Looking'
        negotiating  = 'NEGOTIATING',  'In Negotiation'
        purchased    = 'PURCHASED',    'Purchased'
        not_interested = 'NOT_INTERESTED', 'Not Interested'
        lost         = 'LOST',         'Lost'

    contacted = models.BooleanField(default=False)
    status = models.CharField(choices=Status.choices, default=Status.new, max_length=20)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_leads',
        limit_choices_to={'is_staff': True},
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"
    