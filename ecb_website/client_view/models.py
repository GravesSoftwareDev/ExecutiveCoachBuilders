from django.db import models

# Create your models here.
class Contact(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return f"{self.firstname} {self.lastname} <{self.email}>"
    
