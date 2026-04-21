from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import SiteSettings
from .forms import SiteSettingsForm


# Create your views here.
@staff_member_required(login_url='login')
def site_changes(request):
    # should only be the first object
    settings = SiteSettings.objects.get()
    form = SiteSettingsForm(request.POST, request.FILES, instance=settings)

    if request.method == 'POST':
        if form.is_valid():
            form.save()

    return render(request, "edit_site/site_changes.html", {'form':form})
