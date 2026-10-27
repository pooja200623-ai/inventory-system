"""
Management command to create default user groups and permissions:
- Admin: Full access (superuser or staff with all permissions)
- Staff: Inventory management without delete permissions on products, categories, or suppliers.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventory.models import Category, Supplier, Product
from transactions.models import Purchase, Sale, StockMovement


class Command(BaseCommand):
    help = "Set up default user groups: Admin (full access) and Staff (cannot delete inventory models)."

    def handle(self, *args, **options):
        self.stdout.write("Configuring user groups and permissions...")

        admin_group, created_admin = Group.objects.get_or_create(name="Admin")
        staff_group, created_staff = Group.objects.get_or_create(name="Staff")

        # Admin: All permissions across all inventory & transaction models
        all_models = [Category, Supplier, Product, Purchase, Sale, StockMovement]
        content_types = [ContentType.objects.get_for_model(m) for m in all_models]
        admin_permissions = Permission.objects.filter(content_type__in=content_types)
        admin_group.permissions.set(admin_permissions)

        # Staff: Can view, add, and change categories, suppliers, and products,
        # but CANNOT delete them. Can also add/view purchases and sales.
        staff_permissions = Permission.objects.filter(
            content_type__in=content_types
        ).exclude(
            codename__in=[
                "delete_category",
                "delete_supplier",
                "delete_product",
            ]
        )
        staff_group.permissions.set(staff_permissions)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully configured groups: 'Admin' ({admin_permissions.count()} perms), "
            f"'Staff' ({staff_permissions.count()} perms - delete restricted)."
        ))
