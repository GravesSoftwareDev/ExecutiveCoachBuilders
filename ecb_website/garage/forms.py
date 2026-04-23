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
    Both image and video are optional at the field level so blank extra rows
    don't block submission. has_changed() treats a new row with no file of
    either type as unchanged so the formset skips it entirely.

    The video field was added to allow staff to upload video files alongside
    or instead of photos for each gallery row.
    """
    class Meta:
        model = VehicleImage
        # video was added here to expose the new field in the gallery formset
        fields = ['image', 'video', 'alt_text', 'display_order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Neither field is required so that blank extra rows are silently skipped.
        # Staff must upload at least one file, but that is enforced by has_changed()
        # filtering out completely empty rows before Django tries to save them.
        self.fields['image'].required = False
        self.fields['video'].required = False

    def has_changed(self):
        # Skip validation for new rows where neither an image nor a video was uploaded.
        # Updated from the original single-field check to cover both image and video.
        if not self.instance.pk:
            if not self.files.get(self.add_prefix('image')) and \
               not self.files.get(self.add_prefix('video')):
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
