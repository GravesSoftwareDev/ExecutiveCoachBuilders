from django.contrib import admin
from .models import Vehicle, VehicleImage

# StackedInline lets us edit gallery images directly on the Vehicle detail page
class VehicleImageInline(admin.StackedInline):
    """
    Inline admin for VehicleImage so gallery photos can be managed from the Vehicle page.
    """
    # The model this inline is based on
    model = VehicleImage
    # How many blank extra image slots to show by default
    extra = 1
    # Fields to display in each inline row
    fields = ['image', 'alt_text', 'display_order']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Vehicle model.
    """
    # Attach the gallery image inline so images can be added alongside the vehicle
    inlines = [VehicleImageInline]

    # Columns shown on the Vehicle list page in the admin
    list_display = ['name', 'category', 'passenger_capacity', 'display_order', 'is_published']
    # Sidebar filters to quickly narrow down the vehicle list
    list_filter = ['category', 'is_published']
    # Fields that can be searched from the admin search bar
    search_fields = ['name', 'tagline', 'description']
    # Allows is_published and display_order to be edited directly from the list view
    list_editable = ['is_published', 'display_order']
    # Pre-populates the slug field based on the name field
    prepopulated_fields = {'slug': ('name',)}

@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    """
    Standalone admin for VehicleImage, useful for bulk image management.
    """
    # Columns shown on the VehicleImage list page
    list_display = ['vehicle', 'alt_text', 'display_order']
    # Sidebar filter to narrow images by their parent vehicle
    list_filter = ['vehicle']
    # Allows display_order to be edited directly from the list view
    list_editable = ['display_order']
