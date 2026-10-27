from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('categories/', views.category_list, name='category_list'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('low-stock/', views.low_stock, name='low_stock'),
]
