from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from inventory.models import Product, Supplier


class Purchase(models.Model):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    purchase_date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-purchase_date", "-created_at"]
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"

    def __str__(self):
        return f"Purchase #{self.pk} - {self.supplier.name} ({self.purchase_date})"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_items",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    class Meta:
        verbose_name = "Purchase Item"
        verbose_name_plural = "Purchase Items"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ("PURCHASE", "Purchase"),
        ("SALE", "Sale"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(
        help_text="Positive for stock-in, negative for stock-out.",
    )
    balance_after = models.PositiveIntegerField()
    reference = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"

    def __str__(self):
        sign = "+" if self.quantity > 0 else ""
        return f"{self.product.name} {sign}{self.quantity} ({self.movement_type})"
