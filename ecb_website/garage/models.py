from django.db import models
from django.utils.text import slugify

# Create your models here.

class Vehicle(models.Model):
    """
    Vehicle model creates a table for vehicles in the database. 
    """
    class Category(models.TextChoices):
        """
        Text Choices allows the user to set the data based on limited choices
        """
        LIMO = 'limo','Limousine'
        SHUTTLE = 'shuttle', 'Shuttle Bus'
        MOTORCOACH = 'motorcoach', 'Motorcoach'
        SPRINTER = 'sprinter', 'Sprinter'
        RV = 'recreation', 'Recreation Vehicle'
        CUSTOM = 'custom', 'Custom Vehicle'

    # CharField creates a VarChar field in the table
    name = models.CharField(max_length=120)
    # This gives each Vehicle a unique slug for easier navigation of the website
    slug = models.SlugField(max_length=140, unique=True)
    # VarChar that is determined by the choices available in the Category class. Default is set to Custom.
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.CUSTOM)

    # A short line to catch attention
    tagline = models.CharField(max_length=255, blank=True)
    # A longer bit of text to give more details
    description = models.TextField()
    # An optional field with specific formatting guides for the user
    features = models.TextField(
        blank=True,
        help_text="One feature per line - rendered as a bulleted list."
    )
    # An optional field
    passenger_capacity = models.CharField(
        max_length=40, blank=True
    )

    # The main image of the vehicle
    hero_image = models.ImageField(upload_to='vehicles/')

    # Allows the user to create drafts and publish at a later date.
    is_published = models.BooleanField(default=True)
    # This allows the user to customize the order the vehicles are displayed in based on their marketing priorities.
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        # Vehicles will be ordered in the database by display order first, then by name.
        ordering = ["display_order", "name"]

    # Overides the default string to be the vehicle's name
    def __str__(self):
        return self.name
        
    # This will ensure that if a slug is not manually set then the slug will automatically be the name of the vehicle.
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # Takes the text field of features and creates a list from each individual line in the textfield.
    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]
    
class VehicleImage(models.Model):
    """
    Gallery photos for the detail page (the hero image lives on the vehicle itself).
    """
    # Creates a Foreign Key relationship to Vehicle
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='gallery')
    # Saves an image in the specified directory (blank=True allows video-only rows)
    image = models.ImageField(upload_to="vehicles/", blank=True)
    # Optional video file — supply either image or video (or both)
    video = models.FileField(upload_to="vehicles/", blank=True)
    # Creates alt_text for accessibility
    alt_text = models.CharField(max_length=255, blank=True, help_text="Image or video description")
    # Allows the user to determine the display priority
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

