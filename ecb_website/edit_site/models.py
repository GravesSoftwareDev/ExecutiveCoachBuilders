from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings as Settings

ABOUT_DEFAULT_BODY = (
    "For over 40 years Executive Coach Builders has been your premier luxury limousine and bus builder. "
    "Established in 1976 by John Bumgarner, by 1986 ECB was producing more than 400 limousines a year in an "
    "onsite facility in Springfield MO. Roger Farris took over ownership in 1981 and expanded the operation "
    "throughout the early '80s. In an article published by LCT magazine in 1986, Farris explained that he "
    "approached the Limousine business first as a consumer. Having purchased ECB from Bumgarner, he was drawn "
    "into conversation about buying the company after purchasing a limousine himself. He explained that he was "
    "drawn to ECB because of their distinct quality. Originally specializing in just two limousines, Executive "
    "Coach has since expanded its product offering to more than 25 different vehicles and custom modifications."
    "\n\n"
    "David Bakare, the current owner, took over operation of ECB in 1993 and has since expanded Executive Coach "
    "to be the Premier Luxury Limousine and Bus Builder for the United States and abroad!"
    "\n\n"
    "ECB currently produces around 600 limousines per year. With headquarters located in Springfield, Missouri "
    "ECB provides luxury stretch limousines and buses worldwide. Known as a manufacturer of luxury limousines "
    "from, Ford, Cadillac, Mercedes, Rolls Royce, Bentley, BMW, and Hummer chassis, ECB takes great pride in "
    "delivering quality products."
    "\n\n"
    "With a dedicated and highly experienced staff of employees, ECB has built a reputation as a customer "
    "service oriented company. The plant managers and supervisors alone posess 200 years of experience between "
    "them, working together and applying the knowledge to craft some of the finest vehicles in the business."
    "\n\n"
    "Executive Coach Builders is still committed to high quality vehicle modification and production. Our "
    "vehicles are QVM certified, made in the U.S., modified to fit your needs, and developed with the customer "
    "in mind. With over 40 years of industry experience, Executive Coach Builders is redefining what luxury "
    "transportation should be."
    "\n\n"
    "When it comes to designing and producing limousines, integrity and exceptional industry knowledge make "
    "Executive Coach Builders the only choice. Schedule a visit today to check out our production facility, "
    "or talk to a representative by calling 417-831-3535!"
)


class AboutPage(models.Model):
    title = models.CharField(max_length=200, default="Our Story")
    image = models.ImageField(upload_to="about/", blank=True, null=True)
    body = models.TextField(default=ABOUT_DEFAULT_BODY)

    class Meta:
        verbose_name = "About Page"


class SiteSetting(models.Model):
    name = models.CharField(max_length=100, default="_", blank=True)
    file_value = models.FileField(upload_to='site_settings/', default="_")
    text_value = models.CharField(max_length=255, default="_", blank=True)
    file = models.BooleanField(default="0")

    def get_value(this):
        if this.file:
            if not this.file_value or this.file_value.name == '_':
                return ''
            return this.file_value.url
        return this.text_value
    
    class Meta:
        ordering = ["name"]