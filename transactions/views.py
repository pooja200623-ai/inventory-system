from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q

from inventory.models import Product
from .models import Purchase, PurchaseItem, Sale, SaleItem, StockMovement
from .forms import PurchaseForm, SaleForm, StockAdjustmentForm


# ═════════════════════════════════════════════
#  SHARED HELPERS
# ═════════════════════════════════════════════

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


# ═════════════════════════════════════════════
#  PURCHASE VIEWS
# ═════════════════════════════════════════════

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


@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related("supplier", "created_by").prefetch_related("items__product"),
        pk=pk,
    )
    return render(request, "transactions/purchase_detail.html", {"purchase": purchase})


@login_required
def purchase_create(request):
    products = Product.objects.order_by("name")
    form = PurchaseForm(request.POST or None)

    if request.method == "POST":
        if not form.is_valid():
            messages.error(request, "Please fix the errors below.")
            return render(request, "transactions/purchase_form.html", {
                "form": form,
                "products": products,
            })

        try:
            raw_items = _parse_items(request.POST)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "transactions/purchase_form.html", {
                "form": form,
                "products": products,
            })

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

                    product.quantity += item_data["quantity"]
                    product.purchase_price = item_data["unit_price"]
                    product.save()

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


# ═════════════════════════════════════════════
#  SALE VIEWS
# ═════════════════════════════════════════════

@login_required
def sale_list(request):
    qs = Sale.objects.select_related("created_by").all()

    q = request.GET.get("q", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(customer_name__icontains=q))
    if date_from:
        qs = qs.filter(sale_date__gte=date_from)
    if date_to:
        qs = qs.filter(sale_date__lte=date_to)

    return render(request, "transactions/sale_list.html", {
        "sales": qs,
        "q": q,
        "date_from": date_from,
        "date_to": date_to,
    })


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related("created_by").prefetch_related("items__product"),
        pk=pk,
    )
    return render(request, "transactions/sale_detail.html", {"sale": sale})


@login_required
def sale_invoice(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related("created_by").prefetch_related("items__product"),
        pk=pk,
    )
    return render(request, "transactions/sale_invoice.html", {"sale": sale})


@login_required
def sale_create(request):
    products = Product.objects.order_by("name")
    form = SaleForm(request.POST or None)

    if request.method == "POST":
        if not form.is_valid():
            messages.error(request, "Please fix the errors below.")
            return render(request, "transactions/sale_form.html", {
                "form": form,
                "products": products,
            })

        try:
            raw_items = _parse_items(request.POST)
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "transactions/sale_form.html", {
                "form": form,
                "products": products,
            })

        # ── Combine duplicate products ──
        combined = defaultdict(lambda: {"quantity": 0, "unit_price": Decimal("0")})
        for item in raw_items:
            pid = item["product_id"]
            combined[pid]["quantity"] += item["quantity"]
            combined[pid]["unit_price"] = item["unit_price"]   # keep latest price

        # ── Atomic stock deduction ──
        try:
            with transaction.atomic():
                sale = form.save(commit=False)
                sale.created_by = request.user
                sale.total_amount = 0
                sale.save()   # generates invoice_number

                grand_total = Decimal("0.00")
                low_stock_warnings = []

                for pid, data in combined.items():
                    product = Product.objects.select_for_update().get(pk=pid)

                    if data["quantity"] > product.quantity:
                        raise ValueError(
                            f'Only {product.quantity} unit{"s" if product.quantity != 1 else ""} '
                            f'of "{product.name}" available, but {data["quantity"]} requested.'
                        )

                    line_total = data["quantity"] * data["unit_price"]
                    grand_total += line_total

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=data["quantity"],
                        unit_price=data["unit_price"],
                    )

                    product.quantity -= data["quantity"]
                    product.save()

                    StockMovement.objects.create(
                        product=product,
                        movement_type="SALE",
                        quantity=-data["quantity"],
                        balance_after=product.quantity,
                        reference=f"Sale {sale.invoice_number}",
                        created_by=request.user,
                    )

                    if product.is_low_stock:
                        low_stock_warnings.append(
                            f'"{product.name}" is now low on stock ({product.quantity} remaining, '
                            f"reorder level {product.reorder_level})."
                        )

                sale.total_amount = grand_total
                sale.save()

        except Product.DoesNotExist:
            messages.error(request, "One of the selected products no longer exists.")
            return render(request, "transactions/sale_form.html", {
                "form": form,
                "products": products,
            })
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "transactions/sale_form.html", {
                "form": form,
                "products": products,
            })

        messages.success(request, f"Sale {sale.invoice_number} recorded successfully!")
        for w in low_stock_warnings:
            messages.warning(request, w)

        return redirect("sale_invoice", pk=sale.pk)

    return render(request, "transactions/sale_form.html", {
        "form": form,
        "products": products,
    })


# ═════════════════════════════════════════════
#  STOCK HISTORY & ADJUSTMENTS
# ═════════════════════════════════════════════

@login_required
def stock_history(request):
    movements_qs = StockMovement.objects.select_related("product", "created_by").order_by("-created_at")

    product_id = request.GET.get("product", "").strip()
    movement_type = request.GET.get("movement_type", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if product_id:
        movements_qs = movements_qs.filter(product_id=product_id)
    if movement_type:
        movements_qs = movements_qs.filter(movement_type=movement_type)
    if date_from:
        movements_qs = movements_qs.filter(created_at__date__gte=date_from)
    if date_to:
        movements_qs = movements_qs.filter(created_at__date__lte=date_to)

    paginator = Paginator(movements_qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    products = Product.objects.all().order_by("name")
    selected_product = None
    if product_id:
        try:
            selected_product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            selected_product = None

    return render(request, "transactions/stock_history.html", {
        "page_obj": page_obj,
        "products": products,
        "product_id": product_id,
        "selected_product": selected_product,
        "movement_type": movement_type,
        "date_from": date_from,
        "date_to": date_to,
    })


@login_required
def stock_adjustment(request):
    initial_data = {}
    product_id = request.GET.get("product")
    if product_id:
        initial_data["product"] = product_id

    form = StockAdjustmentForm(request.POST or None, initial=initial_data)

    if request.method == "POST" and form.is_valid():
        product_obj = form.cleaned_data["product"]
        qty = form.cleaned_data["quantity"]
        reason = form.cleaned_data["reason"].strip()

        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=product_obj.pk)
                new_balance = product.quantity + qty

                if new_balance < 0:
                    raise ValueError(
                        f'Cannot reduce {abs(qty)} unit{"s" if abs(qty) != 1 else ""}. '
                        f'Current stock for "{product.name}" is only {product.quantity}.'
                    )

                product.quantity = new_balance
                product.save()

                StockMovement.objects.create(
                    product=product,
                    movement_type="ADJUSTMENT",
                    quantity=qty,
                    balance_after=new_balance,
                    reference=f"Adjustment: {reason}",
                    created_by=request.user,
                )

            messages.success(
                request,
                f'Stock for "{product.name}" adjusted successfully ({"+" if qty > 0 else ""}{qty}). '
                f'New balance: {product.quantity}.'
            )
            return redirect(f"/transactions/stock-history/?product={product.pk}")

        except ValueError as exc:
            messages.error(request, str(exc))
        except Product.DoesNotExist:
            messages.error(request, "Selected product could not be found.")

    return render(request, "transactions/adjustment_form.html", {
        "form": form,
    })

