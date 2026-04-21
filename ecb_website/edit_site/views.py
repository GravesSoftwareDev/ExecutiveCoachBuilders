from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


# Create your views here.
@staff_member_required(login_url='login')
def site_changes(request):
    return render(request, "edit_site/site_changes.html")