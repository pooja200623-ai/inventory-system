# StockPulse — Inventory Management & Sales Analytics System

An enterprise-grade, full-stack Inventory Management and Sales Analytics Web Application built with **Django 5**, **MySQL**, **Bootstrap 5**, and **Chart.js**.

---

## 🚀 Project Overview

**StockPulse** is designed for modern retail, wholesale, and warehouse operations. It streamlines inventory control, purchase order processing, retail point-of-sale invoicing, and stock movement auditing, backed by real-time analytics and financial intelligence.

### Key Highlights
- **ACID Transactions**: Strict database-level row locking (`select_for_update`) ensures inventory counts remain 100% accurate under concurrent orders.
- **Stock Audit Trail**: Immutable logging of every single unit added, sold, or manually adjusted.
- **Role-Based Access Control**: Separation between administrative personnel and floor staff.
- **Visual Analytics**: Interactive dashboards and multi-tab operational reports with instant CSV exports.

---

## 📦 Features (12 Core Modules)

1. **Authentication & Profile Management**
   - User registration, login, logout, and profile management with Django's secure authentication framework.
   - Session tracking and password validation.

2. **Role-Based Access Control (RBAC)**
   - **Admin Group**: Full operational access including adding, editing, and deleting inventory items.
   - **Staff Group**: Operational access to add and edit products, suppliers, categories, purchases, and sales, with protected restrictions preventing deletion of core catalog data.

3. **Category Management (CRUD)**
   - Categorize products with names and descriptions.
   - Dynamic real-time product count per category, search filtering, pagination, and protected deletion blockers preventing orphan items.

4. **Supplier Directory (CRUD)**
   - Track vendors and supplier contact details (phone, email, physical address).
   - Instant search by supplier name, detailed pagination, and protected deletion rules.

5. **Product Catalog (CRUD)**
   - Complete product records: name, unique product code (SKU), category link (`on_delete=models.PROTECT`), purchase price, selling price, stock on hand, and reorder threshold.
   - Search by product name or SKU, filter by category, and automatic red **"Low"** badge indicator.

6. **Low Stock Detection & Restock Alerts**
   - Dedicated low-stock radar (`quantity <= reorder_level`) using database-level F-expressions.
   - Visual badges ("Out of Stock" vs "Low") and 1-click restock purchase actions.

7. **Purchase Management (Stock-In)**
   - Dynamic multi-row order forms powered by JavaScript (auto-filling costs, live line totals, and grand total recalculation).
   - Atomic database transactions with product row locking (`select_for_update`).
   - Automatically increases stock, updates the product's latest purchase price, and creates a positive `StockMovement`.

8. **Sales Management & POS Billing (Stock-Out)**
   - Dynamic item rows displaying live available inventory with client-side quantity checks.
   - Duplicate item consolidation prior to database processing.
   - Stock deduction with automated checks to prevent negative inventory.
   - Generates unique sequential invoice identifiers (`INV-YYYY0001`).

9. **Printable Tax Invoices**
   - Clean, professional invoice layout displaying company metadata, customer information, itemized table, and total amounts.
   - Custom print stylesheets (`@media print`) that automatically hide web navigation bars and controls for clean PDF/paper printing.

10. **Stock Movement Audit Trail & Manual Adjustments**
    - Chronological log of all inventory movements with colored badges (**PURCHASE** in green, **SALE** in red, **ADJUSTMENT** in orange).
    - Multi-criteria filtering by product, movement type, and date range with 20 items per page pagination.
    - **Manual Stock Adjustment**: Handle inventory shrinkage, damages, or count reconciliations with mandatory reason auditing and negative balance prevention.

11. **Real-time Executive Dashboard**
    - High-level metric cards: Total Products, Total Stock Units, This Month's Sales ($), This Month's Purchases ($), and Low-Stock Alert Count.
    - Chart.js visualizations:
      - 6-month monthly sales vs purchases trend (grouped bar chart).
      - Top 5 best-selling products by volume (horizontal bar chart).
      - Revenue breakdown by product category (doughnut chart).
    - Quick-access tables for recent sales invoices and critical low-stock items.

12. **Analytics & Financial Reports with CSV Export**
    - Multi-tab analytics console with date range filtering:
      1. **Daily Sales Report**: Aggregated by day using `TruncDate` with order counts and totals.
      2. **Monthly Sales Report**: Monthly sales volume using `TruncMonth`.
      3. **Purchase Summary**: Two-way aggregation (by supplier and by purchase date).
      4. **Current Stock Valuation**: Itemized stock valuation calculated as `quantity * purchase_price`.
      5. **Estimated Profit Report**: Itemized gross profit calculation using `(unit_price - purchase_price) * quantity`.
    - Dedicated **"Export CSV"** button on every report view generating clean, timestamped spreadsheets.

---

## 🛠 Tech Stack

- **Backend**: Python 3.11+, Django 5.2 (MVT architecture)
- **Database**: MySQL 8.x via `mysqlclient` (Strict SQL mode enabled)
- **Configuration**: `python-decouple` (12-Factor App methodology)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Data Visualization**: Chart.js 4.4+ (safe payload delivery via `json_script`)

---

## 🗄 Entity-Relationship (ER) Architecture

```
+------------------+         +------------------+         +--------------------+
|     Category     | 1     * |     Product      | 1     * |     StockMovement  |
+------------------+---------+------------------+---------+--------------------+
| id (PK)          |         | id (PK)          |         | id (PK)            |
| name (Unique)    |         | product_code (UQ)|         | product_id (FK)    |
| description      |         | category_id (FK) |         | movement_type      |
| created_at       |         | purchase_price   |         | quantity (signed)  |
+------------------+         | selling_price    |         | balance_after      |
                             | quantity         |         | reference          |
+------------------+         | reorder_level    |         | created_by (FK)    |
|     Supplier     |         | created_at       |         | created_at         |
+------------------+         +--------+---------+         +--------------------+
| id (PK)          |                  | 1
| name             |                  |
| phone / email    |         +--------+---------+         +--------------------+
| address          |         |                  |         |     SaleItem       |
+--------+---------+         |                  | 1     * +--------------------+
         | 1                 |                  +---------+ id (PK)            |
         |                   |                            | sale_id (FK)       |
         | *                 | *                          | product_id (FK)    |
+--------+---------+     +---+--------------+             | quantity           |
|     Purchase     | 1 * |   PurchaseItem   |             | unit_price         |
+------------------+-----+------------------+             +---------+----------+
| id (PK)          |     | id (PK)          |                       | *
| supplier_id (FK) |     | purchase_id (FK) |                       | 1
| purchase_date    |     | product_id (FK)  |             +---------+----------+
| total_amount     |     | quantity         |             |       Sale         |
| created_by (FK)  |     | unit_price       |             +--------------------+
| created_at       |     +------------------+             | id (PK)            |
+------------------+                                      | invoice_number (UQ)|
                                                          | customer_name      |
                                                          | sale_date          |
                                                          | total_amount       |
                                                          | created_by (FK)    |
                                                          | created_at         |
                                                          +--------------------+
```

---

## ⚙️ Setup & Installation Instructions

### 1. Prerequisites
- Python 3.11 or higher
- MySQL Server 8.0+ running locally or remotely

### 2. Clone the Repository & Set Up Virtual Environment
```bash
# Clone the repository
git clone <repository_url>
cd Inventory

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure MySQL Database & Environment Variables
Create a database in your MySQL server:
```sql
CREATE DATABASE inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Create a `.env` file in the root directory (referencing `.env.example`):
```env
SECRET_KEY=your-secure-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=inventory_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 4. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Initialize Roles & Seed Sample Data
```bash
# Set up RBAC user groups (Admin & Staff)
python manage.py setup_roles

# Populate database with 4 categories, 3 suppliers, and 15 sample products
python manage.py seed_inventory

# Create an administrator superuser
python manage.py createsuperuser
```

### 6. Start Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser and log in with your credentials.

---

## 🧪 Running Automated Unit Tests

Run the test suite covering atomic purchases, stock reductions, out-of-stock validation, rollbacks, and sequential movement balances:
```bash
python manage.py test transactions.tests
```

---

## 📸 Screenshots & Previews

*(Place application UI screenshots in `docs/screenshots/`)*

| Screen | Description | Placeholder |
|---|---|---|
| **Executive Dashboard** | Real-time KPI summary cards, sales vs purchases trend, top products bar chart, and category doughnut | `![Dashboard](docs/screenshots/dashboard.png)` |
| **Product Inventory** | Paginated catalog table with category filters, search bar, and low stock indicators | `![Products](docs/screenshots/products.png)` |
| **POS Sales & Invoice** | Dynamic order builder with stock validation and print-optimized tax invoice layout | `![Invoice](docs/screenshots/invoice.png)` |
| **Stock Movement Audit** | Color-coded movement logs, filtering tools, and manual stock adjustment modal | `![Audit Trail](docs/screenshots/stock_history.png)` |
| **Financial Reports** | Daily/monthly sales, supplier purchases, inventory valuation, and profit margins | `![Analytics](docs/screenshots/reports.png)` |

---

## 📄 License
This project is licensed under the MIT License.
