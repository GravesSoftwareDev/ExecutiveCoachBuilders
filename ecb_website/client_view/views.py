from django.shortcuts import redirect, render, get_object_or_404
from edit_site.models import SiteSetting, AboutPage
from .forms import ContactForm
from garage.models import Vehicle
from blog.models import Article
from django.http import HttpResponseRedirect
from .models import Service

def home(request):
    published = Vehicle.objects.filter(is_published=True)

    # Best sellers: any vehicle given display_order=0 — the highest marketing priority.
    # Set a vehicle's display_order to 1 or higher in the admin to keep it out of this row.
    best_sellers = published.filter(display_order=0)

    # Load settings
    site_settings_model = SiteSetting.objects.all()
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
        'all_vehicles': published,
        'site_settings': site_settings
    })


def vehicle_detail(request, slug):
    vehicle = get_object_or_404(Vehicle, slug=slug, is_published=True)
    all_gallery = vehicle.gallery.all()
    # Split into separate lists so the template can render a clean photo grid
    # followed by a dedicated full-width video section, rather than mixing them.
    photos = [item for item in all_gallery if item.image and not item.video]
    videos = [item for item in all_gallery if item.video]
    return render(request, 'client_view/vehicle_detail.html', {
        'vehicle': vehicle,
        'photos': photos,
        'videos': videos,
    })

def about(request):
    about, _ = AboutPage.objects.get_or_create(pk=1)
    return render(request, 'client_view/about.html', {'about': about})

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_view:thankyou_contact')
    else:
        form = ContactForm()
    return render(request, 'client_view/contact.html', {'form': form})

def coaches(request):
    published = Vehicle.objects.filter(is_published=True, used_vehicle=False)
    return render(request, 'client_view/coaches.html', {
        'all_vehicles': published,
    })

def used_vehicle(request):
    published = Vehicle.objects.filter(is_published=True, used_vehicle=True)
    return render(request, 'client_view/used_vehicle.html', {
        'all_vehicles': published,
    })

def services(request):
    services = Service.objects.all()
    return render(request, "client_view/services.html", {'services': services})

def thankyou_contact(request):
    return render(request, 'client_view/thankyou_contact.html')


def article_list(request):
    articles = Article.publisher.all()
    return render(request, 'client_view/article_list.html', {'articles': articles})


def article_detail(request, year, month, slug):
    article = get_object_or_404(
        Article,
        status=Article.Status.PUBLISHED,
        publish__year=year,
        publish__month=month,
        slug=slug,
    )
    return render(request, 'client_view/article_detail.html', {'article': article})
