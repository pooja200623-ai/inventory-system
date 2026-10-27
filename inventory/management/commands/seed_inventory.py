"""
Management command to seed sample data:
  - 4 Categories (Notebooks, Pens, Pencils, Files)
  - 3 Suppliers
  - 15 Products
"""

from django.core.management.base import BaseCommand
from inventory.models import Category, Supplier, Product


CATEGORIES = [
    {"name": "Notebooks", "description": "All types of notebooks and journals"},
    {"name": "Pens", "description": "Ballpoint, gel, and fountain pens"},
    {"name": "Pencils", "description": "Graphite and coloured pencils"},
    {"name": "Files", "description": "Folders, binders, and filing accessories"},
]

SUPPLIERS = [
    {
        "name": "OfficeWorld Supplies",
        "phone": "+1-555-101-2020",
        "email": "sales@officeworld.example.com",
        "address": "12 Commerce Drive, Suite 100, New York, NY 10001",
    },
    {
        "name": "PaperMart Distributors",
        "phone": "+1-555-202-3030",
        "email": "info@papermart.example.com",
        "address": "45 Industrial Ave, Chicago, IL 60601",
    },
    {
        "name": "StationeryHub Ltd.",
        "phone": "+1-555-303-4040",
        "email": "orders@stationeryhub.example.com",
        "address": "78 Trade Boulevard, Los Angeles, CA 90001",
    },
]

PRODUCTS = [
    # Notebooks
    {"name": "A4 Spiral Notebook", "product_code": "NB-001", "category": "Notebooks", "purchase_price": "1.50", "selling_price": "3.99", "quantity": 120, "reorder_level": 20},
    {"name": "A5 Hardcover Journal", "product_code": "NB-002", "category": "Notebooks", "purchase_price": "2.80", "selling_price": "6.50", "quantity": 8, "reorder_level": 15},
    {"name": "B5 Ruled Notepad (50 sheets)", "product_code": "NB-003", "category": "Notebooks", "purchase_price": "0.90", "selling_price": "2.25", "quantity": 5, "reorder_level": 10},
    {"name": "Pocket Memo Pad", "product_code": "NB-004", "category": "Notebooks", "purchase_price": "0.50", "selling_price": "1.20", "quantity": 200, "reorder_level": 30},
    # Pens
    {"name": "Ballpoint Pen Blue (Box/12)", "product_code": "PN-001", "category": "Pens", "purchase_price": "3.00", "selling_price": "7.50", "quantity": 60, "reorder_level": 10},
    {"name": "Gel Ink Pen Black 0.5mm", "product_code": "PN-002", "category": "Pens", "purchase_price": "0.80", "selling_price": "2.00", "quantity": 7, "reorder_level": 10},
    {"name": "Fountain Pen Classic", "product_code": "PN-003", "category": "Pens", "purchase_price": "5.50", "selling_price": "12.99", "quantity": 25, "reorder_level": 5},
    {"name": "Whiteboard Marker Red", "product_code": "PN-004", "category": "Pens", "purchase_price": "0.60", "selling_price": "1.50", "quantity": 3, "reorder_level": 5},
    # Pencils
    {"name": "HB Pencil (Box/12)", "product_code": "PC-001", "category": "Pencils", "purchase_price": "1.20", "selling_price": "2.99", "quantity": 150, "reorder_level": 20},
    {"name": "Coloured Pencils Set (24)", "product_code": "PC-002", "category": "Pencils", "purchase_price": "4.00", "selling_price": "9.99", "quantity": 9, "reorder_level": 10},
    {"name": "Mechanical Pencil 0.7mm", "product_code": "PC-003", "category": "Pencils", "purchase_price": "1.10", "selling_price": "2.75", "quantity": 40, "reorder_level": 10},
    {"name": "Charcoal Sketching Pencil", "product_code": "PC-004", "category": "Pencils", "purchase_price": "0.90", "selling_price": "2.20", "quantity": 4, "reorder_level": 8},
    # Files
    {"name": "A4 Lever Arch File", "product_code": "FL-001", "category": "Files", "purchase_price": "1.80", "selling_price": "4.50", "quantity": 75, "reorder_level": 15},
    {"name": "Polypropylene A4 Folder", "product_code": "FL-002", "category": "Files", "purchase_price": "0.70", "selling_price": "1.75", "quantity": 6, "reorder_level": 10},
    {"name": "Expanding File 13-Pocket", "product_code": "FL-003", "category": "Files", "purchase_price": "2.50", "selling_price": "5.99", "quantity": 30, "reorder_level": 10},
]


class Command(BaseCommand):
    help = "Seed the database with sample categories, suppliers, and products."

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")
        cat_map = {}
        for data in CATEGORIES:
            obj, created = Category.objects.get_or_create(name=data["name"], defaults={"description": data["description"]})
            cat_map[obj.name] = obj
            status = "created" if created else "already exists"
            self.stdout.write(f"  Category '{obj.name}' — {status}")

        self.stdout.write("Seeding suppliers...")
        for data in SUPPLIERS:
            obj, created = Supplier.objects.get_or_create(name=data["name"], defaults={
                "phone": data["phone"],
                "email": data["email"],
                "address": data["address"],
            })
            status = "created" if created else "already exists"
            self.stdout.write(f"  Supplier '{obj.name}' — {status}")

        self.stdout.write("Seeding products...")
        for data in PRODUCTS:
            category = cat_map.get(data["category"])
            if not category:
                self.stderr.write(f"  Category '{data['category']}' not found, skipping product '{data['name']}'")
                continue
            obj, created = Product.objects.get_or_create(
                product_code=data["product_code"],
                defaults={
                    "name": data["name"],
                    "category": category,
                    "purchase_price": data["purchase_price"],
                    "selling_price": data["selling_price"],
                    "quantity": data["quantity"],
                    "reorder_level": data["reorder_level"],
                },
            )
            status = "created" if created else "already exists"
            self.stdout.write(f"  Product '{obj.name}' — {status}")

        self.stdout.write(self.style.SUCCESS("Seed complete!"))
