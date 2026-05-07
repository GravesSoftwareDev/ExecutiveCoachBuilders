from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def portal_section_required(perm_field):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_staff:
                return redirect('login')
            if not request.user.is_portal_admin and not getattr(request.user, perm_field, False):
                messages.error(request, "You don't have permission to access this section.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def portal_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('login')
        if not request.user.is_portal_admin:
            messages.error(request, "Admin access required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
