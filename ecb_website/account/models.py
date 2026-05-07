from django.contrib.auth.models import AbstractUser
from django.db import models


class Employee(AbstractUser):
    class Role(models.TextChoices):
        agent = 'AGENT', 'Agent'
        admin = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.agent,
    )
    can_edit_site = models.BooleanField(default=False)
    can_edit_fleet = models.BooleanField(default=False)
    can_edit_blog = models.BooleanField(default=False)
    can_edit_services = models.BooleanField(default=False)
    can_edit_team = models.BooleanField(default=False)

    @property
    def is_portal_admin(self):
        return self.role == self.Role.admin or self.is_superuser
