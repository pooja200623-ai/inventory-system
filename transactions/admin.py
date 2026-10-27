from django.contrib import admin
from .models import Purchase, PurchaseItem, Sale, SaleItem, StockMovement


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    readonly_fields = ("line_total",)

    @admin.display(description="Line Total")
    def line_total(self, obj):
        if obj.pk:
            return f"${obj.line_total:,.2f}"
        return "-"


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("__str__", "supplier", "purchase_date", "total_amount", "created_by", "created_at")
    list_filter = ("purchase_date", "supplier")
    search_fields = ("supplier__name",)
    readonly_fields = ("total_amount", "created_by", "created_at")
    inlines = [PurchaseItemInline]


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ("purchase", "product", "quantity", "unit_price")
    list_filter = ("purchase",)
    search_fields = ("product__name",)


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("line_total",)

    @admin.display(description="Line Total")
    def line_total(self, obj):
        if obj.pk:
            return f"${obj.line_total:,.2f}"
        return "-"


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer_name", "sale_date", "total_amount", "created_by", "created_at")
    list_filter = ("sale_date",)
    search_fields = ("invoice_number", "customer_name")
    readonly_fields = ("invoice_number", "total_amount", "created_by", "created_at")
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ("sale", "product", "quantity", "unit_price")
    list_filter = ("sale",)
    search_fields = ("product__name",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity", "balance_after", "reference", "created_by", "created_at")
    list_filter = ("movement_type", "created_at")
    search_fields = ("product__name", "reference")
    readonly_fields = ("created_at",)
