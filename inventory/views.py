from django.shortcuts import render
from django.http import HttpResponse

# Placeholder views for Inventory app (to be implemented in subsequent steps)

def product_list(request):
    return HttpResponse("Product list placeholder")

def category_list(request):
    return HttpResponse("Category list placeholder")

def supplier_list(request):
    return HttpResponse("Supplier list placeholder")

def low_stock(request):
    return HttpResponse("Low stock placeholder")
