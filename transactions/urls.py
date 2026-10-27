from django.urls import path
from . import views

urlpatterns = [
    # Purchases
    path("purchases/", views.purchase_list, name="purchase_list"),
    path("purchases/create/", views.purchase_create, name="purchase_create"),
    path("purchases/<int:pk>/", views.purchase_detail, name="purchase_detail"),

    # Sales (placeholder)
    path("sales/", views.sale_list, name="sale_list"),

    # Stock history
    path("stock-history/", views.stock_history, name="stock_history"),
]
