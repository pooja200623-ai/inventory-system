from django import forms
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
