from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from inventory.models import Product
from .models import Purchase, PurchaseItem, StockMovement
from .forms import PurchaseForm


# ─────────────────────────────────────────────
# Purchase list  (with optional date filter)
# ─────────────────────────────────────────────

@login_required
def purchase_list(request):
    qs = Purchase.objects.select_related("supplier", "created_by").all()

    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    if date_from:
        qs = qs.filter(purchase_date__gte=date_from)
    if date_to:
        qs = qs.filter(purchase_date__lte=date_to)

    return render(request, "transactions/purchase_list.html", {
        "purchases": qs,
        "date_from": date_from,
        "date_to": date_to,
    })


# ─────────────────────────────────────────────
# Purchase detail
# ─────────────────────────────────────────────

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related("supplier", "created_by").prefetch_related("items__product"),
        pk=pk,
    )
    return render(request, "transactions/purchase_detail.html", {"purchase": purchase})


# ─────────────────────────────────────────────
# Create purchase  (header + dynamic item rows)
# ─────────────────────────────────────────────

def _parse_items(post_data):
    """Extract item rows from the POST payload.

    Returns a list of dicts: [{ product_id, quantity, unit_price }, ...]
    Raises ValueError with a user-facing message on bad data.
    """
    product_ids = post_data.getlist("item_product[]")
    quantities = post_data.getlist("item_quantity[]")
    unit_prices = post_data.getlist("item_unit_price[]")

    if not product_ids:
        raise ValueError("You must add at least one product row.")

    items = []
    for i, (pid, qty, price) in enumerate(zip(product_ids, quantities, unit_prices), 1):
        pid = pid.strip()
        qty = qty.strip()
        price = price.strip()

        if not pid or not qty or not price:
            raise ValueError(f"Row {i}: all fields (product, quantity, unit price) are required.")

        try:
            pid = int(pid)
        except (ValueError, TypeError):
            raise ValueError(f"Row {i}: invalid product selection.")

        try:
            qty = int(qty)
            if qty < 1:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError(f"Row {i}: quantity must be a positive whole number.")

        try:
            price = Decimal(price)
            if price <= 0:
                raise ValueError()
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Row {i}: unit price must be a positive number.")

        items.append({"product_id": pid, "quantity": qty, "unit_price": price})

    return items


@login_required
def purchase_create(request):
    products = Product.objects.order_by("name")
    form = PurchaseForm(request.POST or None)

    if request.method == "POST":
        # --- validate header ---
        if not form.is_valid():
            messages.error(request, "Please fix the errors below.")
            return render(request, "transactions/purchase_form.html", {
                "form": form,
                "products": products,
            })

        # --- validate items ---
        try:
            raw_items = _parse_items(request.POST)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "transactions/purchase_form.html", {
                "form": form,
                "products": products,
            })

        # --- atomic stock update ---
        try:
            with transaction.atomic():
                purchase = form.save(commit=False)
                purchase.created_by = request.user
                purchase.total_amount = 0
                purchase.save()

                grand_total = Decimal("0.00")

                for item_data in raw_items:
                    product = Product.objects.select_for_update().get(pk=item_data["product_id"])

                    line_total = item_data["quantity"] * item_data["unit_price"]
                    grand_total += line_total

                    PurchaseItem.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                    )

                    # Update stock
                    product.quantity += item_data["quantity"]
                    product.purchase_price = item_data["unit_price"]
                    product.save()

                    # Record stock movement
                    StockMovement.objects.create(
                        product=product,
                        movement_type="PURCHASE",
                        quantity=item_data["quantity"],
                        balance_after=product.quantity,
                        reference=f"Purchase #{purchase.pk}",
                        created_by=request.user,
                    )

                purchase.total_amount = grand_total
                purchase.save()

        except Product.DoesNotExist:
            messages.error(request, "One of the selected products no longer exists.")
            return render(request, "transactions/purchase_form.html", {
                "form": form,
                "products": products,
            })

        messages.success(request, f"Purchase #{purchase.pk} recorded successfully.")
        return redirect("purchase_detail", pk=purchase.pk)

    return render(request, "transactions/purchase_form.html", {
        "form": form,
        "products": products,
    })


# ─────────────────────────────────────────────
# Stock History (placeholder kept working)
# ─────────────────────────────────────────────

@login_required
def stock_history(request):
    movements = StockMovement.objects.select_related("product", "created_by").all()[:200]
    return render(request, "transactions/stock_history.html", {"movements": movements})


# ─────────────────────────────────────────────
# Sale list  (placeholder – to be built later)
# ─────────────────────────────────────────────

@login_required
def sale_list(request):
    from django.http import HttpResponse
    return HttpResponse("Sale list placeholder")
