from django.shortcuts import redirect, render, get_object_or_404
from .forms import contactForm
from edit_site.models import SiteSettings
from garage.models import Vehicle
from django.http import HttpResponseRedirect
from django.conf import settings as Settings


def home(request):
    published = Vehicle.objects.filter(is_published=True)

    # Best sellers: any vehicle given display_order=0 — the highest marketing priority.
    # Set a vehicle's display_order to 1 or higher in the admin to keep it out of this row.
    best_sellers = published.filter(display_order=0)

    # Load settings
    site_settings_model = SiteSettings.objects.all()
    site_settings = {s.name : s.get_value() for s in site_settings_model}

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
        'site_settings': site_settings
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

def about(request):
    return render(request, 'client_view/about.html')

def contact(request):
    if request.method == "POST":
        form = contactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_view:thankyou_contact')
    else:
        form = contactForm()
    return render(request, 'client_view/contact.html', {'form': form})

def coaches(request):
    return render(request, 'client_view/coaches.html')

def services(request):
    return render(request, 'client_view/services.html')

def thankyou_contact(request):
    return render(request, 'client_view/thankyou_contact.html')
