from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def can_delete_inventory_required(view_func):
    """
    Decorator that checks if the logged-in user has permission to delete inventory items.
    Users in the 'Staff' group (who are not superusers/Admin) are blocked with a friendly message.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('login')

        # Superusers and Admins are always allowed
        if user.is_superuser or user.groups.filter(name='Admin').exists():
            return view_func(request, *args, **kwargs)

        # If user is in Staff group (or lacks delete permission)
        if user.groups.filter(name='Staff').exists() or not user.has_perm('inventory.delete_product'):
            messages.error(
                request,
                "Permission Denied: Staff members are not authorized to delete inventory records. "
                "Please contact an administrator."
            )
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
