from django import forms
from .models import Category, Supplier, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional description"}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone", "email", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Supplier name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+1 (555) 000-0000"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "supplier@example.com"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Full address"}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "product_code", "category", "purchase_price", "selling_price", "quantity", "reorder_level"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Product name"}),
            "product_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. SKU-001"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
            "selling_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "reorder_level": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }

    def clean_purchase_price(self):
        val = self.cleaned_data.get("purchase_price")
        if val is not None and val <= 0:
            raise forms.ValidationError("Purchase price must be a positive number.")
        return val

    def clean_selling_price(self):
        val = self.cleaned_data.get("selling_price")
        if val is not None and val <= 0:
            raise forms.ValidationError("Selling price must be a positive number.")
        return val
