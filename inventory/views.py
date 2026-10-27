from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, ProtectedError

from .models import Category, Supplier, Product
from .forms import CategoryForm, SupplierForm, ProductForm


# ─────────────────────────────────────────────
# Category Views
# ─────────────────────────────────────────────

@login_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(request, "inventory/category_list.html", {"categories": categories})


@login_required
def category_add(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category created successfully.")
        return redirect("category_list")
    return render(request, "inventory/category_form.html", {"form": form, "action": "Add"})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect("category_list")
    return render(request, "inventory/category_form.html", {"form": form, "action": "Edit", "object": category})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        try:
            category.delete()
            messages.success(request, f'Category "{category.name}" deleted successfully.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete "{category.name}" because it is assigned to one or more products. '
                "Please reassign or remove those products first.",
            )
        return redirect("category_list")
    return render(request, "inventory/category_confirm_delete.html", {"object": category})


# ─────────────────────────────────────────────
# Supplier Views
# ─────────────────────────────────────────────

@login_required
def supplier_list(request):
    q = request.GET.get("q", "").strip()
    suppliers = Supplier.objects.all()
    if q:
        suppliers = suppliers.filter(name__icontains=q)
    return render(request, "inventory/supplier_list.html", {"suppliers": suppliers, "q": q})


@login_required
def supplier_add(request):
    form = SupplierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Supplier added successfully.")
        return redirect("supplier_list")
    return render(request, "inventory/supplier_form.html", {"form": form, "action": "Add"})


@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Supplier updated successfully.")
        return redirect("supplier_list")
    return render(request, "inventory/supplier_form.html", {"form": form, "action": "Edit", "object": supplier})


@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.delete()
        messages.success(request, f'Supplier "{supplier.name}" deleted successfully.')
        return redirect("supplier_list")
    return render(request, "inventory/supplier_confirm_delete.html", {"object": supplier})


# ─────────────────────────────────────────────
# Product Views
# ─────────────────────────────────────────────

@login_required
def product_list(request):
    q = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()

    products = Product.objects.select_related("category").all()
    if q:
        products = products.filter(name__icontains=q) | products.filter(product_code__icontains=q)
        products = products.distinct()
    if category_id:
        products = products.filter(category_id=category_id)

    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    return render(request, "inventory/product_list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "q": q,
        "selected_category": category_id,
    })


@login_required
def product_add(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product created successfully.")
        return redirect("product_list")
    return render(request, "inventory/product_form.html", {"form": form, "action": "Add"})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect("product_list")
    return render(request, "inventory/product_form.html", {"form": form, "action": "Edit", "object": product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        try:
            product.delete()
            messages.success(request, f'Product "{product.name}" deleted successfully.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete "{product.name}" because it is referenced by existing transactions. '
                "Please remove those transactions first.",
            )
        return redirect("product_list")
    return render(request, "inventory/product_confirm_delete.html", {"object": product})


# ─────────────────────────────────────────────
# Low Stock View
# ─────────────────────────────────────────────

@login_required
def low_stock(request):
    products = Product.objects.filter(quantity__lte=F("reorder_level")).select_related("category").order_by("name")
    return render(request, "inventory/low_stock.html", {"products": products})
