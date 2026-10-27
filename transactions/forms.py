from django import forms
from inventory.models import Product
from .models import Purchase, Sale


class PurchaseForm(forms.ModelForm):
    """Header form for the purchase (supplier + date)."""

    class Meta:
        model = Purchase
        fields = ["supplier", "purchase_date"]
        widgets = {
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "purchase_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["purchase_date"].input_formats = ["%Y-%m-%d"]


class SaleForm(forms.ModelForm):
    """Header form for the sale (customer name + date)."""

    class Meta:
        model = Sale
        fields = ["customer_name", "sale_date"]
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Customer name"}),
            "sale_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sale_date"].input_formats = ["%Y-%m-%d"]


class StockAdjustmentForm(forms.Form):
    """Form for manual inventory stock adjustments."""

    product = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by("name"),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label="-- Select Product --",
    )
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. +5 to add, -3 to deduct",
        }),
        help_text="Enter a positive number to add stock, or a negative number to reduce stock.",
    )
    reason = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. Damaged during handling, Inventory count correction, Lost item",
        }),
        max_length=255,
        required=True,
        help_text="Mandatory explanation for this adjustment.",
    )

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty == 0:
            raise forms.ValidationError("Adjustment quantity cannot be zero.")
        return qty
