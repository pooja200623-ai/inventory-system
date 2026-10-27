from django.urls import path
from . import views

urlpatterns = [
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('sales/', views.sale_list, name='sale_list'),
    path('stock-history/', views.stock_history, name='stock_history'),
]
