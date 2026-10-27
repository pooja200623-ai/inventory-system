from django.urls import path
from . import views

urlpatterns = [
    # Purchases
    path("purchases/", views.purchase_list, name="purchase_list"),
    path("purchases/create/", views.purchase_create, name="purchase_create"),
    path("purchases/<int:pk>/", views.purchase_detail, name="purchase_detail"),

    # Sales
    path("sales/", views.sale_list, name="sale_list"),
    path("sales/create/", views.sale_create, name="sale_create"),
    path("sales/<int:pk>/", views.sale_detail, name="sale_detail"),
    path("sales/<int:pk>/invoice/", views.sale_invoice, name="sale_invoice"),

    # Stock history
    path("stock-history/", views.stock_history, name="stock_history"),
]
