from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from inventory.models import Category, Supplier, Product
from transactions.models import Purchase, PurchaseItem, Sale, SaleItem, StockMovement

User = get_user_model()


class TransactionsBusinessLogicTestCase(TestCase):
    def setUp(self):
        # 1. User setup
        self.user = User.objects.create_user(
            username="testuser",
            password="Password123!",
            email="test@example.com",
        )
        self.client = Client()
        self.client.login(username="testuser", password="Password123!")

        # 2. Category & Supplier setup
        self.category = Category.objects.create(name="Stationery", description="All stationery")
        self.supplier = Supplier.objects.create(
            name="Alpha Supplies",
            phone="1234567890",
            email="alpha@example.com",
            address="123 Alpha Way",
        )

        # 3. Product setup
        self.product = Product.objects.create(
            name="Ballpoint Pen",
            product_code="PEN-001",
            category=self.category,
            purchase_price=Decimal("1.00"),
            selling_price=Decimal("2.50"),
            quantity=10,
            reorder_level=5,
        )

    def test_purchase_increases_stock_and_updates_price(self):
        """Test that recording a purchase increases product quantity and updates purchase_price."""
        url = reverse("purchase_create")
        post_data = {
            "supplier": self.supplier.pk,
            "purchase_date": "2026-10-28",
            "item_product[]": [self.product.pk],
            "item_quantity[]": [15],
            "item_unit_price[]": ["1.25"],
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        self.product.refresh_from_db()
        # 10 initial + 15 purchased = 25
        self.assertEqual(self.product.quantity, 25)
        self.assertEqual(self.product.purchase_price, Decimal("1.25"))

        # Verify Purchase & Items
        purchase = Purchase.objects.latest("created_at")
        self.assertEqual(purchase.total_amount, Decimal("18.75"))

        # Verify StockMovement
        movement = StockMovement.objects.filter(product=self.product, movement_type="PURCHASE").latest("created_at")
        self.assertEqual(movement.quantity, 15)
        self.assertEqual(movement.balance_after, 25)

    def test_sale_decreases_stock(self):
        """Test that recording a valid sale decreases product quantity."""
        url = reverse("sale_create")
        post_data = {
            "customer_name": "John Doe",
            "sale_date": "2026-10-28",
            "item_product[]": [self.product.pk],
            "item_quantity[]": [4],
            "item_unit_price[]": ["2.50"],
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        self.product.refresh_from_db()
        # 10 initial - 4 sold = 6
        self.assertEqual(self.product.quantity, 6)

        sale = Sale.objects.latest("created_at")
        self.assertEqual(sale.total_amount, Decimal("10.00"))

        movement = StockMovement.objects.filter(product=self.product, movement_type="SALE").latest("created_at")
        self.assertEqual(movement.quantity, -4)
        self.assertEqual(movement.balance_after, 6)

    def test_sale_blocked_when_stock_insufficient(self):
        """Test that sale is blocked when requested quantity exceeds available inventory."""
        initial_stock = self.product.quantity  # 10
        url = reverse("sale_create")
        post_data = {
            "customer_name": "Big Buyer",
            "sale_date": "2026-10-28",
            "item_product[]": [self.product.pk],
            "item_quantity[]": [20],  # only 10 available
            "item_unit_price[]": ["2.50"],
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)  # Re-renders form with error
        self.assertContains(response, "available, but 20 requested")

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, initial_stock)
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(StockMovement.objects.filter(movement_type="SALE").count(), 0)

    def test_atomic_rollback_on_failure(self):
        """
        Test that if one item in a multi-item purchase or sale fails (e.g. insufficient stock for second product),
        the whole transaction rolls back and no partial records or stock updates persist.
        """
        product2 = Product.objects.create(
            name="Drawing Compass",
            product_code="CMP-002",
            category=self.category,
            purchase_price=Decimal("2.00"),
            selling_price=Decimal("4.00"),
            quantity=2,
            reorder_level=5,
        )

        url = reverse("sale_create")
        post_data = {
            "customer_name": "Multi Buyer",
            "sale_date": "2026-10-28",
            "item_product[]": [self.product.pk, product2.pk],
            "item_quantity[]": [5, 10],  # product 1 has 10 (ok), but product 2 only has 2 (fails!)
            "item_unit_price[]": ["2.50", "4.00"],
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)

        # Neither product stock should change
        self.product.refresh_from_db()
        product2.refresh_from_db()
        self.assertEqual(self.product.quantity, 10)
        self.assertEqual(product2.quantity, 2)

        # No sale or stock movement created
        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(SaleItem.objects.count(), 0)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_stock_movement_balance_after_is_correct(self):
        """Test that consecutive purchase, sale, and adjustment properly calculate balance_after sequentially."""
        # 1. Purchase +5 -> balance 15
        self.client.post(reverse("purchase_create"), {
            "supplier": self.supplier.pk,
            "purchase_date": "2026-10-28",
            "item_product[]": [self.product.pk],
            "item_quantity[]": [5],
            "item_unit_price[]": ["1.00"],
        })
        m1 = StockMovement.objects.filter(product=self.product).order_by("-created_at")[0]
        self.assertEqual(m1.movement_type, "PURCHASE")
        self.assertEqual(m1.balance_after, 15)

        # 2. Sale -3 -> balance 12
        self.client.post(reverse("sale_create"), {
            "customer_name": "Alice",
            "sale_date": "2026-10-28",
            "item_product[]": [self.product.pk],
            "item_quantity[]": [3],
            "item_unit_price[]": ["2.50"],
        })
        m2 = StockMovement.objects.filter(product=self.product).order_by("-created_at")[0]
        self.assertEqual(m2.movement_type, "SALE")
        self.assertEqual(m2.balance_after, 12)

        # 3. Manual Adjustment -2 -> balance 10
        self.client.post(reverse("stock_adjustment"), {
            "product": self.product.pk,
            "quantity": -2,
            "reason": "Damaged goods discarded",
        })
        m3 = StockMovement.objects.filter(product=self.product).order_by("-created_at")[0]
        self.assertEqual(m3.movement_type, "ADJUSTMENT")
        self.assertEqual(m3.balance_after, 10)

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 10)
