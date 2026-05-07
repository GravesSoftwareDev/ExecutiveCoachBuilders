from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse

# Create your models here.
class Publisher(models.Manager):
    """Custom manager that returns only published articles."""
    def get_queryset(self):
        return (
            super().get_queryset().filter(status=Article.Status.PUBLISHED)
        )


class Article(models.Model):
    """
    Attributes:
        image: Featured image for the article
        title: Article headline
        slug: URL-friendly identifier (unique per publish date)
        author: Foreign key to User who wrote the article
        body: Full article text (supports markdown)
        publish: Publication date/time
        status: Draft or Published state
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DF','Draft'
        PUBLISHED = 'PB','Published'

    image = models.ImageField(upload_to='blog/', blank=True)
    video = models.FileField(upload_to='blog/videos/', blank=True)
    title = models.CharField(max_length=250)
    slug = models.CharField(max_length=250, unique_for_date='publish')
    summary = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Short excerpt for the public news list and search previews.',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='newshroom_articles'
    )
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=2,
        choices=Status,
        default=Status.DRAFT
    )
 
    # Two managers: 'objects' for all articles, 'publisher' for published only
    objects = models.Manager()
    publisher = Publisher()
    
    class Meta:
        ordering = ['-publish']  # Newest articles first
        indexes = [
            models.Index(fields=['-publish']),  # Speed up sorting by most recent
        ]

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse(
            'client_view:article_detail',
            args=[
                self.publish.year,
                self.publish.month,
                self.slug
            ]
        )
