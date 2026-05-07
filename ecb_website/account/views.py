from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from account.models import Lead


@login_required
def dashboard(request):
    if request.user.is_portal_admin:
        leads = Lead.objects.select_related('assigned_to').order_by('last_name', 'first_name')
    else:
        leads = Lead.objects.select_related('assigned_to').filter(assigned_to=request.user).order_by('last_name', 'first_name')

    agents = get_user_model().objects.filter(is_staff=True).order_by('username')
    return render(request, 'account/dashboard.html', {
        'section': 'dashboard',
        'leads':   leads,
        'agents':  agents,
    })


@login_required
@require_POST
def lead_update(request, pk):
    lead = Lead.objects.get(pk=pk)
    field = request.POST.get('field')

    if field == 'contacted':
        lead.contacted = request.POST.get('value') == 'true'
        lead.save(update_fields=['contacted'])
    elif field == 'status':
        valid = [c[0] for c in Lead.Status.choices]
        value = request.POST.get('value')
        if value in valid:
            lead.status = value
            lead.save(update_fields=['status'])
        else:
            return JsonResponse({'ok': False, 'error': 'Invalid status'}, status=400)
    elif field == 'assigned_to':
        value = request.POST.get('value')
        if value:
            lead.assigned_to = get_user_model().objects.filter(pk=value, is_staff=True).first()
        else:
            lead.assigned_to = None
        lead.save(update_fields=['assigned_to'])
    else:
        return JsonResponse({'ok': False, 'error': 'Unknown field'}, status=400)

    return JsonResponse({'ok': True})
