from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Vehicle
from .forms import VehicleForm, VehicleImageFormSet
from account.decorators import portal_section_required


@portal_section_required('can_edit_fleet')
def vehicle_list(request):
    """Shows all vehicles in a table with edit and delete actions."""
    # Order by display_order then name so the list matches the public carousel order
    vehicles = Vehicle.objects.all()
    return render(request, 'garage/vehicle_list.html', {'vehicles': vehicles})


@portal_section_required('can_edit_fleet')
def vehicle_add(request):
    """Handles the blank Add Vehicle form and its gallery image formset."""
    if request.method == 'POST':
        form    = VehicleForm(request.POST, request.FILES)
        formset = VehicleImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            vehicle = form.save()
            # Bind the saved vehicle to the gallery images before saving them
            formset.instance = vehicle
            formset.save()
            messages.success(request, f'"{vehicle.name}" has been added to the fleet.')
            return redirect('garage:vehicle_list')
    else:
        form    = VehicleForm()
        formset = VehicleImageFormSet()

    return render(request, 'garage/vehicle_form.html', {
        'form':    form,
        'formset': formset,
        'action':  'Add New Vehicle',
    })


@portal_section_required('can_edit_fleet')
def vehicle_edit(request, pk):
    """Pre-populates the form with an existing vehicle so staff can update it."""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form    = VehicleForm(request.POST, request.FILES, instance=vehicle)
        formset = VehicleImageFormSet(request.POST, request.FILES, instance=vehicle)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'"{vehicle.name}" has been updated.')
            return redirect('garage:vehicle_list')
    else:
        form    = VehicleForm(instance=vehicle)
        formset = VehicleImageFormSet(instance=vehicle)

    return render(request, 'garage/vehicle_form.html', {
        'form':    form,
        'formset': formset,
        'vehicle': vehicle,
        'action':  f'Edit — {vehicle.name}',
    })


@portal_section_required('can_edit_fleet')
def vehicle_delete(request, pk):
    """Shows a confirmation page; deletes the vehicle on POST."""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        name = vehicle.name
        vehicle.delete()
        messages.success(request, f'"{name}" has been removed from the fleet.')
        return redirect('garage:vehicle_list')
    return render(request, 'garage/vehicle_confirm_delete.html', {'vehicle': vehicle})
