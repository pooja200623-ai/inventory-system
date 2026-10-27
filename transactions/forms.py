from django import forms
from .models import Purchase


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
