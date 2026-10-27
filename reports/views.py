from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Views for Reports & Dashboard


@login_required
def dashboard(request):
    """Main dashboard — requires an authenticated session."""
    return render(request, 'reports/dashboard.html')


@login_required
def reports_view(request):
    return HttpResponse("Reports view placeholder")
