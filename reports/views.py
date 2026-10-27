import csv
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from inventory.models import Category, Product
from transactions.models import Purchase, PurchaseItem, Sale, SaleItem


# ═════════════════════════════════════════════
#  DASHBOARD VIEW
# ═════════════════════════════════════════════

@login_required
def dashboard(request):
    today = timezone.localdate()
    first_of_this_month = today.replace(day=1)

    # 1. Summary Cards
    total_products = Product.objects.count()
    total_stock_units = Product.objects.aggregate(total_units=Coalesce(Sum('quantity'), 0))['total_units']

    month_sales_amount = Sale.objects.filter(
        sale_date__gte=first_of_this_month,
        sale_date__lte=today,
    ).aggregate(total=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))))['total']

    month_purchase_amount = Purchase.objects.filter(
        purchase_date__gte=first_of_this_month,
        purchase_date__lte=today,
    ).aggregate(total=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))))['total']

    low_stock_products = Product.objects.filter(
        quantity__lte=F('reorder_level')
    ).select_related('category').order_by('quantity')
    low_stock_count = low_stock_products.count()

    # 2. Charts Data
    # 2a. Last 6 months Sales vs Purchases (by month)
    months_labels = []
    # Build a list of the start dates for the last 6 calendar months in chronological order
    cur_year = today.year
    cur_month = today.month
    month_starts = []
    for i in range(5, -1, -1):
        m = cur_month - i
        y = cur_year
        while m <= 0:
            m += 12
            y -= 1
        m_start = date(y, m, 1)
        month_starts.append(m_start)
        months_labels.append(m_start.strftime('%b %Y'))

    earliest_month = month_starts[0]

    sales_by_month_qs = Sale.objects.filter(
        sale_date__gte=earliest_month
    ).annotate(
        m=TruncMonth('sale_date')
    ).values('m').annotate(
        total=Coalesce(Sum('total_amount'), Value(Decimal('0.00')))
    )
    sales_month_map = {item['m'].strftime('%b %Y'): float(item['total']) for item in sales_by_month_qs if item['m']}

    purchases_by_month_qs = Purchase.objects.filter(
        purchase_date__gte=earliest_month
    ).annotate(
        m=TruncMonth('purchase_date')
    ).values('m').annotate(
        total=Coalesce(Sum('total_amount'), Value(Decimal('0.00')))
    )
    purchases_month_map = {item['m'].strftime('%b %Y'): float(item['total']) for item in purchases_by_month_qs if item['m']}

    sales_trend_data = [sales_month_map.get(lbl, 0.0) for lbl in months_labels]
    purchases_trend_data = [purchases_month_map.get(lbl, 0.0) for lbl in months_labels]

    # 2b. Top 5 selling products (by total quantity sold)
    top_selling_qs = SaleItem.objects.values(
        'product__name', 'product__product_code'
    ).annotate(
        total_qty=Coalesce(Sum('quantity'), 0),
        total_revenue=Coalesce(Sum(F('quantity') * F('unit_price')), Value(Decimal('0.00'))),
    ).order_by('-total_qty')[:5]

    top_products_labels = [f"{item['product__name']} ({item['product__product_code']})" for item in top_selling_qs]
    top_products_qty = [int(item['total_qty']) for item in top_selling_qs]

    # 2c. Sales by category (doughnut)
    sales_by_cat_qs = SaleItem.objects.values(
        'product__category__name'
    ).annotate(
        total_amount=Coalesce(Sum(F('quantity') * F('unit_price')), Value(Decimal('0.00')))
    ).order_by('-total_amount')

    cat_labels = [item['product__category__name'] or 'Uncategorized' for item in sales_by_cat_qs]
    cat_data = [float(item['total_amount']) for item in sales_by_cat_qs]

    # 3. Recent 5 Sales & Mini Low Stock Table
    recent_sales = Sale.objects.select_related('created_by').order_by('-created_at')[:5]
    low_stock_mini = low_stock_products[:5]

    chart_payload = {
        'months_labels': months_labels,
        'sales_trend': sales_trend_data,
        'purchases_trend': purchases_trend_data,
        'top_products_labels': top_products_labels,
        'top_products_qty': top_products_qty,
        'cat_labels': cat_labels,
        'cat_data': cat_data,
    }

    context = {
        'total_products': total_products,
        'total_stock_units': total_stock_units,
        'month_sales_amount': month_sales_amount,
        'month_purchase_amount': month_purchase_amount,
        'low_stock_count': low_stock_count,
        'chart_payload': chart_payload,
        'recent_sales': recent_sales,
        'low_stock_mini': low_stock_mini,
    }
    return render(request, 'reports/dashboard.html', context)


# ═════════════════════════════════════════════
#  REPORTS & CSV EXPORTS
# ═════════════════════════════════════════════

@login_required
def reports_view(request):
    today = timezone.localdate()
    default_from = today - timedelta(days=30)

    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()
    active_tab = request.GET.get('tab', 'daily_sales').strip()

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else default_from
    except ValueError:
        date_from = default_from

    try:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except ValueError:
        date_to = today

    # 1. Daily Sales Report
    daily_sales_qs = Sale.objects.filter(
        sale_date__gte=date_from,
        sale_date__lte=date_to,
    ).annotate(
        day=TruncDate('sale_date')
    ).values('day').annotate(
        orders_count=Count('id', distinct=True),
        total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
    ).order_by('-day')

    daily_totals = daily_sales_qs.aggregate(
        total_orders=Coalesce(Sum('orders_count'), 0),
        total_sales=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
    )

    # 2. Monthly Sales Report
    monthly_sales_qs = Sale.objects.filter(
        sale_date__gte=date_from,
        sale_date__lte=date_to,
    ).annotate(
        month=TruncMonth('sale_date')
    ).values('month').annotate(
        orders_count=Count('id', distinct=True),
        total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
    ).order_by('-month')

    monthly_totals = monthly_sales_qs.aggregate(
        total_orders=Coalesce(Sum('orders_count'), 0),
        total_sales=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
    )

    # 3. Purchase Summary (By Supplier & By Date)
    # 3a. By Supplier
    supplier_summary_qs = Purchase.objects.filter(
        purchase_date__gte=date_from,
        purchase_date__lte=date_to,
    ).values(
        'supplier__name', 'supplier__phone', 'supplier__email'
    ).annotate(
        orders_count=Count('id', distinct=True),
        total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
    ).order_by('-total_amount')

    # 3b. By Date
    purchase_by_date_qs = Purchase.objects.filter(
        purchase_date__gte=date_from,
        purchase_date__lte=date_to,
    ).annotate(
        day=TruncDate('purchase_date')
    ).values('day').annotate(
        orders_count=Count('id', distinct=True),
        total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
    ).order_by('-day')

    purchase_totals = Purchase.objects.filter(
        purchase_date__gte=date_from,
        purchase_date__lte=date_to,
    ).aggregate(
        total_orders=Count('id', distinct=True),
        total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
    )

    # 4. Current Stock Report (stock value = quantity x purchase_price)
    stock_items_qs = Product.objects.select_related('category').annotate(
        stock_value=ExpressionWrapper(
            F('quantity') * F('purchase_price'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    ).order_by('name')

    stock_totals = stock_items_qs.aggregate(
        total_quantity=Coalesce(Sum('quantity'), 0),
        total_value=Coalesce(
            Sum(F('quantity') * F('purchase_price')),
            Value(Decimal('0.00')),
        ),
    )

    # 5. Estimated Profit: sum((unit_price - product.purchase_price) x quantity)
    sold_items_qs = SaleItem.objects.filter(
        sale__sale_date__gte=date_from,
        sale__sale_date__lte=date_to,
    ).select_related('product', 'product__category', 'sale').annotate(
        unit_cost=F('product__purchase_price'),
        cost_total=ExpressionWrapper(
            F('quantity') * F('product__purchase_price'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        selling_total=ExpressionWrapper(
            F('quantity') * F('unit_price'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        profit=ExpressionWrapper(
            (F('unit_price') - F('product__purchase_price')) * F('quantity'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    ).order_by('-sale__sale_date', '-sale__created_at')

    profit_totals = sold_items_qs.aggregate(
        total_qty=Coalesce(Sum('quantity'), 0),
        total_revenue=Coalesce(Sum(F('quantity') * F('unit_price')), Value(Decimal('0.00'))),
        total_cost=Coalesce(Sum(F('quantity') * F('product__purchase_price')), Value(Decimal('0.00'))),
        total_profit=Coalesce(
            Sum((F('unit_price') - F('product__purchase_price')) * F('quantity')),
            Value(Decimal('0.00')),
        ),
    )

    context = {
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'active_tab': active_tab,
        'daily_sales': daily_sales_qs,
        'daily_totals': daily_totals,
        'monthly_sales': monthly_sales_qs,
        'monthly_totals': monthly_totals,
        'supplier_summary': supplier_summary_qs,
        'purchase_by_date': purchase_by_date_qs,
        'purchase_totals': purchase_totals,
        'stock_items': stock_items_qs,
        'stock_totals': stock_totals,
        'sold_items': sold_items_qs,
        'profit_totals': profit_totals,
    }
    return render(request, 'reports/reports.html', context)


# ═════════════════════════════════════════════
#  CSV EXPORT VIEWS
# ═════════════════════════════════════════════

@login_required
def export_csv_view(request):
    report_type = request.GET.get('type', 'daily_sales')
    today = timezone.localdate()
    default_from = today - timedelta(days=30)

    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else default_from
    except ValueError:
        date_from = default_from

    try:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except ValueError:
        date_to = today

    response = HttpResponse(content_type='text/csv')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

    if report_type == 'daily_sales':
        response['Content-Disposition'] = f'attachment; filename="daily_sales_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Orders Count', 'Total Sales Amount ($)'])

        daily_qs = Sale.objects.filter(
            sale_date__gte=date_from,
            sale_date__lte=date_to,
        ).annotate(
            day=TruncDate('sale_date')
        ).values('day').annotate(
            orders_count=Count('id', distinct=True),
            total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
        ).order_by('-day')

        for row in daily_qs:
            writer.writerow([
                row['day'].strftime('%Y-%m-%d') if row['day'] else '',
                row['orders_count'],
                f"{row['total_amount']:.2f}",
            ])

    elif report_type == 'monthly_sales':
        response['Content-Disposition'] = f'attachment; filename="monthly_sales_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Month', 'Orders Count', 'Total Sales Amount ($)'])

        monthly_qs = Sale.objects.filter(
            sale_date__gte=date_from,
            sale_date__lte=date_to,
        ).annotate(
            month=TruncMonth('sale_date')
        ).values('month').annotate(
            orders_count=Count('id', distinct=True),
            total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
        ).order_by('-month')

        for row in monthly_qs:
            writer.writerow([
                row['month'].strftime('%B %Y') if row['month'] else '',
                row['orders_count'],
                f"{row['total_amount']:.2f}",
            ])

    elif report_type == 'purchases_supplier':
        response['Content-Disposition'] = f'attachment; filename="purchases_by_supplier_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Supplier Name', 'Phone', 'Email', 'Orders Count', 'Total Purchased ($)'])

        supplier_qs = Purchase.objects.filter(
            purchase_date__gte=date_from,
            purchase_date__lte=date_to,
        ).values(
            'supplier__name', 'supplier__phone', 'supplier__email'
        ).annotate(
            orders_count=Count('id', distinct=True),
            total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
        ).order_by('-total_amount')

        for row in supplier_qs:
            writer.writerow([
                row['supplier__name'] or 'N/A',
                row['supplier__phone'] or '',
                row['supplier__email'] or '',
                row['orders_count'],
                f"{row['total_amount']:.2f}",
            ])

    elif report_type == 'purchases_date':
        response['Content-Disposition'] = f'attachment; filename="purchases_by_date_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Orders Count', 'Total Purchased ($)'])

        purch_date_qs = Purchase.objects.filter(
            purchase_date__gte=date_from,
            purchase_date__lte=date_to,
        ).annotate(
            day=TruncDate('purchase_date')
        ).values('day').annotate(
            orders_count=Count('id', distinct=True),
            total_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
        ).order_by('-day')

        for row in purch_date_qs:
            writer.writerow([
                row['day'].strftime('%Y-%m-%d') if row['day'] else '',
                row['orders_count'],
                f"{row['total_amount']:.2f}",
            ])

    elif report_type == 'current_stock':
        response['Content-Disposition'] = f'attachment; filename="current_stock_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Product Code', 'Product Name', 'Category', 'Quantity',
            'Purchase Price ($)', 'Selling Price ($)', 'Total Stock Value ($)', 'Status'
        ])

        stock_items = Product.objects.select_related('category').annotate(
            stock_value=ExpressionWrapper(
                F('quantity') * F('purchase_price'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        ).order_by('name')

        for p in stock_items:
            status = 'Low Stock' if p.is_low_stock else 'OK'
            writer.writerow([
                p.product_code,
                p.name,
                p.category.name if p.category else 'N/A',
                p.quantity,
                f"{p.purchase_price:.2f}",
                f"{p.selling_price:.2f}",
                f"{p.stock_value:.2f}",
                status,
            ])

    elif report_type == 'profit':
        response['Content-Disposition'] = f'attachment; filename="estimated_profit_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Invoice #', 'Product Code', 'Product Name', 'Quantity',
            'Unit Purchase Cost ($)', 'Unit Selling Price ($)',
            'Total Cost ($)', 'Total Sales ($)', 'Estimated Profit ($)'
        ])

        sold_items = SaleItem.objects.filter(
            sale__sale_date__gte=date_from,
            sale__sale_date__lte=date_to,
        ).select_related('product', 'sale').annotate(
            cost_total=ExpressionWrapper(
                F('quantity') * F('product__purchase_price'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            selling_total=ExpressionWrapper(
                F('quantity') * F('unit_price'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            profit=ExpressionWrapper(
                (F('unit_price') - F('product__purchase_price')) * F('quantity'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        ).order_by('-sale__sale_date', '-sale__created_at')

        for item in sold_items:
            writer.writerow([
                item.sale.sale_date.strftime('%Y-%m-%d'),
                item.sale.invoice_number,
                item.product.product_code,
                item.product.name,
                item.quantity,
                f"{item.product.purchase_price:.2f}",
                f"{item.unit_price:.2f}",
                f"{item.cost_total:.2f}",
                f"{item.selling_total:.2f}",
                f"{item.profit:.2f}",
            ])
    else:
        response['Content-Disposition'] = f'attachment; filename="report_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', 'Invalid report type requested'])

    return response
