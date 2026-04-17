from django.shortcuts import render, get_object_or_404
from garage.models import Vehicle


def home(request):
    published = Vehicle.objects.filter(is_published=True)

    # Best sellers: any vehicle given display_order=0 — the highest marketing priority.
    # Set a vehicle's display_order to 1 or higher in the admin to keep it out of this row.
    best_sellers = published.filter(display_order=0)

    # Build one (label, queryset) pair per category that actually has published vehicles
    category_groups = []
    for value, label in Vehicle.Category.choices:
        group = published.filter(category=value)
        if group.exists():
            category_groups.append((label, group))

    return render(request, 'client_view/home.html', {
        'best_sellers': best_sellers,
        'category_groups': category_groups,
        # Full list used by the browse-all grid at the bottom of the page
        'all_vehicles': published,
    })


def vehicle_detail(request, slug):
    # Only allow published vehicles to be viewed publicly
    vehicle = get_object_or_404(Vehicle, slug=slug, is_published=True)
    # Gallery images are pre-fetched and already ordered by display_order via model Meta
    gallery = vehicle.gallery.all()
    return render(request, 'client_view/vehicle_detail.html', {
        'vehicle': vehicle,
        'gallery': gallery,
    })
