from django.contrib import admin
from .models import Category, Supplier, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "email", "phone")
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_code", "category", "purchase_price", "selling_price", "quantity", "reorder_level", "is_low_stock", "updated_at")
    list_filter = ("category",)
    search_fields = ("name", "product_code")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="Low Stock?")
    def is_low_stock(self, obj):
        return obj.is_low_stock
