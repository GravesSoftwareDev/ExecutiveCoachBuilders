from django import forms
from django.forms import inlineformset_factory
from .models import Vehicle, VehicleImage


class VehicleForm(forms.ModelForm):
    """
    ModelForm for creating and editing a Vehicle.
    Slug is shown so staff can override it, but help text explains it auto-fills.
    """
    class Meta:
        model = Vehicle
        fields = [
            'name', 'slug', 'category',
            'tagline', 'description', 'features',
            'passenger_capacity', 'hero_image',
            'is_published', 'display_order',
        ]
        widgets = {
            # Multi-line widgets for the longer text fields
            'description': forms.Textarea(attrs={'rows': 5}),
            'features':    forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'slug':              'Auto-filled from the vehicle name. Only edit if you need a custom URL.',
            'features':          'Enter one feature per line — the site will display them as a bulleted list.',
            'display_order':     'Lower numbers appear first. Set to 0 to include this vehicle in the Best Sellers carousel.',
            'is_published':      'Uncheck to save as a draft — the vehicle will not appear on the public site.',
            'passenger_capacity':'Optional. Example: "12–16 passengers".',
            'hero_image':        'Main display image for listing and detail pages.',
        }


class VehicleImageForm(forms.ModelForm):
    """
    Form used inside the gallery image formset.
    Image is set to not required so that blank extra rows don't block submission.
    has_changed() is overridden to treat a blank extra row (no file selected,
    no existing instance) as unchanged — this stops display_order's default
    value of 0 from tricking Django into validating an otherwise empty row.
    """
    class Meta:
        model = VehicleImage
        fields = ['image', 'alt_text', 'display_order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow the form to submit without an image so blank extra rows are skipped
        self.fields['image'].required = False

    def has_changed(self):
        # If this is a brand-new (unsaved) row with no file uploaded, treat it
        # as empty so the formset skips validation and doesn't try to save it
        if not self.instance.pk:
            file_key = self.add_prefix('image')
            if not self.files.get(file_key):
                return False
        return super().has_changed()


# Inline formset lets staff manage gallery photos on the same page as the vehicle
VehicleImageFormSet = inlineformset_factory(
    Vehicle,
    VehicleImage,
    form=VehicleImageForm,  # Use the custom form so blank rows are ignored
    extra=2,
    can_delete=True,
)
