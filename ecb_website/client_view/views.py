import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from blog.models import Article
from blog.render import render_article_html
from edit_site.models import AboutPage, SiteSetting
from garage.models import Vehicle
from leads.services import ingest_inbound_form

from .forms import ContactForm
from .models import Service, TeamMember


def _contact_initial(request):
    source = (
        request.GET.get('src')
        or request.GET.get('vehicle')
        or request.GET.get('service')
        or 'website_contact'
    )
    if request.GET.get('vehicle'):
        source = f"vehicle:{request.GET['vehicle']}"
    elif request.GET.get('service'):
        source = f"service:{request.GET['service']}"
    return {
        'source': str(source)[:80],
        'source_url': str(request.META.get('HTTP_REFERER') or request.get_full_path())[:255],
    }


def home(request):
    published = Vehicle.objects.filter(is_published=True)
    best_sellers = published.filter(display_order=0)
    site_settings_model = SiteSetting.objects.all()
    site_settings = {s.name: s.get_value() for s in site_settings_model}

    category_groups = []
    for value, label in Vehicle.Category.choices:
        group = published.filter(category=value)
        if group.exists():
            category_groups.append((label, group))

    return render(request, 'client_view/home.html', {
        'best_sellers': best_sellers,
        'category_groups': category_groups,
        'all_vehicles': published,
        'site_settings': site_settings,
    })


def vehicle_detail(request, slug):
    vehicle = get_object_or_404(Vehicle, slug=slug, is_published=True)
    all_gallery = vehicle.gallery.all()
    photos = [item for item in all_gallery if item.image and not item.video]
    videos = [item for item in all_gallery if item.video]
    return render(request, 'client_view/vehicle_detail.html', {
        'vehicle': vehicle,
        'photos': photos,
        'videos': videos,
    })


def about(request):
    about_page, _ = AboutPage.objects.get_or_create(pk=1)
    team_members = TeamMember.objects.filter(is_active=True)
    return render(request, 'client_view/about.html', {
        'about': about_page,
        'team_members': team_members,
    })


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            ingest_inbound_form(form.cleaned_data)
            return redirect('client_view:thankyou_contact')
    else:
        form = ContactForm(initial=_contact_initial(request))
    return render(request, 'client_view/contact.html', {'form': form})


def coaches(request):
    published = Vehicle.objects.filter(is_published=True, used_vehicle=False)
    return render(request, 'client_view/coaches.html', {'all_vehicles': published})


def used_vehicle(request):
    published = Vehicle.objects.filter(is_published=True, used_vehicle=True)
    return render(request, 'client_view/used_vehicle.html', {'all_vehicles': published})


def services(request):
    services_qs = Service.objects.all().order_by("display_order")
    return render(request, "client_view/services.html", {'services': services_qs})


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
    return render(request, 'client_view/article_detail.html', {
        'article': article,
        'article_html': render_article_html(article.body),
    })


@require_POST
def public_chat(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}

    message = (payload.get('message') or '').strip()
    history = payload.get('history') if isinstance(payload.get('history'), list) else []
    if not message:
        return JsonResponse({'reply': 'Please type a question so I can help.'}, status=400)

    from agent.public_chat import answer_public_question

    reply = answer_public_question(message, history)
    if not reply:
        reply = (
            'The chat assistant is not configured yet. Please use the contact form '
            'or call the ECB team for help with your build.'
        )
    return JsonResponse({'reply': reply})
