from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/export-csv/', views.export_csv_view, name='export_csv'),
]
