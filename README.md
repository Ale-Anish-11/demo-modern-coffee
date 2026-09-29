# Modern Coffee Shop — E-Commerce Platform

A complete, modern, responsive coffee shop e-commerce web platform built with **Python & Django**, **Tailwind CSS**, **Khalti Sandbox Payment Gateway**, **Pay at Counter**, **Customer Loyalty / Points System**, and **Staff / Owner Management Analytics**.

---

## 🌟 Key Features

### 1. Modern Coffee-Shop Aesthetic & Responsive UI
- **Design Philosophy:** Warm coffee-inspired visual style (espresso roasts, creamy foam, golden amber hues).
- **Frontend Stack:** Clean semantic HTML5, **Tailwind CSS** (responsive grid, custom palette), and vanilla JavaScript.
- **Icons & Typography:** FontAwesome 6 icons + Google Fonts (*Playfair Display* & *Plus Jakarta Sans*).
- **Dynamic Navigation:** Context-aware navigation bar adapting between Guests, Authenticated Customers, and Staff / Store Owners.
- **Components:** Interactive coffee cards, category pills, search & filtering, live cart counter, toasts, and sticky checkout summaries.

### 2. Robust Customer Authentication & Security
- Built upon **Django's native authentication system** (`django.contrib.auth`).
- **Registration Form:** Validates full name, unique username, unique email, phone number, and strong passwords via Django's password validators.
- **Welcome Reward:** Awards **50 bonus loyalty points** automatically upon registration.
- **Login:** Supports authentication via **either username or email** address with a "Remember Me" session option (2-week session vs browser close).
- **Security:**
  - 100% CSRF protected (`{% csrf_token %}` on all mutating forms).
  - Passwords hashed using PBKDF2 with SHA256 (no plaintext passwords).
  - Object-level authorization prevents customers from viewing or modifying other customers' orders, profiles, receipts, or points.
  - All secret keys and payment gateway tokens are isolated in `.env` (excluded by `.gitignore`).

### 3. Coffee Menu, Search & Real-Time Filtering
- **Categories:** Espresso, Cappuccino, Latte, Americano, Mocha, Cold Coffee, Tea & Matcha, Snacks & Bakery, Desserts.
- **Search & Sort:** Instant query filtering by name, taste profile, or category slug. Sort by Featured, Popular, Highest Rated, and Price (Low to High / High to Low).
- **Stock Guarding:** Products show real-time stock levels (*"Only 3 left"*, *"Out of Stock"*). Prevents ordering or adding items exceeding inventory limits.
- **Nutritional & Brewing Insights:** Displays calories, approximate brewing times, and customer review scores.

### 4. Server-Side Shopping Cart
- Session-backed cart (`orders/cart.py`) that **never trusts prices submitted by client browsers**.
- Re-fetches latest product models from the database on every calculation.
- Increment/decrement quantity controls clamped to live inventory stock.
- Calculates subtotal and previews potential loyalty points to be earned upon order completion.

### 5. Dual Checkout Options
- **Option 1 — Khalti Sandbox (Test Payment Gateway):**
  - Integrates with the official Khalti ePayment API v2 (`initiate/` and backend `lookup/`).
  - Calls payment initiation with amount in paisa and purchase order reference.
  - Upon user completion, Khalti calls the backend return URL (`payments:khalti_verify`).
  - Backend verifies status with Khalti servers before marking order as `PAID` and `CONFIRMED`.
  - Includes a dedicated sandbox test portal for zero-friction local simulation.
- **Option 2 — Pay at Counter:**
  - Immediate order creation with `payment_method = 'COUNTER'` and `payment_status = 'PENDING'`.
  - Assigns unique order number (e.g. `MCS-20260929-ABC123`).
  - Instructs customer to collect coffee at the pickup counter and pay via Cash, Card, or Fonepay QR.

### 6. Customer Points / Loyalty Program
- **Configurable Earning Ratio:** Every Rs. 100 spent = 10 points (configurable via `LOYALTY_POINTS_PER_HUNDRED` in `.env`).
- **Points Redemption:** 1 point = Rs. 1.00 cash discount.
- **Backend Validation:** Validates points balance securely within atomic database transactions to eliminate tampering.
- **Ledger Audit:** Complete transactional ledger recording earned points, redeemed discounts, welcome bonuses, and refunds.
- **Membership Tiers:** Bronze Sip, Silver Brew, Gold Roast, and Platinum Reserve perks.

### 7. Printable Receipts & Order History
- **Confirmation Page:** Detailed breakdown of items, unit costs, subtotal, loyalty discount, total payable, and payment status badges.
- **Printable Order Receipt:** Clean printer-optimized invoice (`@media print`) with barista coffee shop header, date/time, tax details, itemized table, and barcode hash.
- **Order History:** Complete chronologically sorted archive of user orders.

### 8. Staff / Owner Management Dashboard
- Accessible to staff and superusers at `/dashboard/staff/`.
- **Live Statistics Cards:**
  - Total Sales (Rs.) from paid orders
  - Today's Orders
  - Pending Barista Queue
  - Completed Orders
  - Active Menu Items
  - Registered Customers
  - Total Loyalty Points Issued
- **Order Management:** Filter by order status (Pending, Confirmed, Preparing, Ready, Completed, Cancelled) and update statuses in real-time.
- **Product Inventory Management:** Add new coffees, edit prices, adjust stock, toggle availability, and upload photos.
- **Customer Directory:** View customer order counts and loyalty points balances.
- **Payment Transaction Log:** Comprehensive log of payment gateway transaction IDs, reference IDs, amounts, and statuses.

---

## 📁 Project Architecture

```text
modern-coffee-shop/
│
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── config/                      # Project Configuration
│   ├── __init__.py
│   ├── settings.py              # Environment variables, apps, templates, auth
│   ├── urls.py                  # Global URL routing
│   ├── views.py                 # Home, About, Contact, 404, 500
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                    # Customer Authentication & Profiles
│   ├── models.py                # CustomerProfile model & signals
│   ├── forms.py                 # Registration, Login, Profile forms
│   ├── views.py                 # Register, Login, Logout, Profile views
│   ├── urls.py
│   ├── admin.py                 # Inlined Profile UserAdmin
│   └── management/commands/
│       └── seed_data.py         # Database seeding script
│
├── products/                    # Coffee Catalog & Categories
│   ├── models.py                # Category & Product models
│   ├── views.py                 # Menu list & Product detail views
│   ├── urls.py
│   └── admin.py
│
├── orders/                      # Shopping Cart & Order Processing
│   ├── cart.py                  # Server-side Cart session manager
│   ├── models.py                # Order & OrderItem models
│   ├── views.py                 # Cart, Checkout, Confirmation, Receipt, History
│   ├── urls.py
│   ├── admin.py
│   └── context_processors.py    # Cart item count & subtotal context
│
├── payments/                    # Khalti Sandbox & Gateway Handling
│   ├── models.py                # Payment transaction model
│   ├── services.py              # Khalti API initiation & backend verification
│   ├── views.py                 # Khalti initiate, verify callback & sandbox simulator
│   ├── urls.py
│   └── admin.py
│
├── loyalty/                     # Rewards Program & Loyalty Points
│   ├── models.py                # LoyaltyPointTransaction ledger model
│   ├── services.py              # Configurable points calculation & redemption
│   ├── views.py                 # Customer rewards dashboard & tiers view
│   ├── urls.py
│   ├── admin.py
│   └── context_processors.py    # Live points balance context
│
├── dashboard/                   # Customer Dashboard & Staff Portal
│   ├── forms.py                 # Admin ProductForm and CategoryForm
│   ├── views.py                 # Customer dashboard, staff analytics, orders, inventory
│   └── urls.py
│
├── templates/                   # Reusable HTML5 Templates
│   ├── base.html                # Base layout, navbar, footer, messages
│   ├── home.html                # Homepage with hero, specials, testimonials
│   ├── about.html               # Coffee roastery story & heritage
│   ├── contact.html             # Store hours, address & contact form
│   ├── 404.html                 # Custom 404 page
│   ├── 500.html                 # Custom 500 page
│   ├── accounts/                # register.html, login.html, profile.html
│   ├── products/                # list.html, detail.html
│   ├── orders/                  # cart.html, checkout.html, confirmation.html, receipt.html, history.html, detail.html
│   ├── payments/                # khalti_sandbox_gateway.html
│   ├── loyalty/                 # rewards.html
│   └── dashboard/               # customer_dashboard.html, admin/ (overview, orders, products, customers, payments)
│
├── static/                      # Static assets (css, js, images)
│   ├── css/style.css
│   └── js/main.js
│
└── media/                       # Uploaded coffee images
```

---

## 🚀 Quickstart & Setup Guide

### 1. Clone & Set Up Virtual Environment

```bash
# Navigate to the project directory
cd demo-modern-coffee

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the sample environment file to `.env`:

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

Verify your `.env` contains:

```env
SECRET_KEY=django-insecure-modern-coffee-shop-secret-key-prod-safe-2026
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,*

DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# Khalti Sandbox Credentials
KHALTI_PUBLIC_KEY=test_public_key_77ca48e7786144e0bcf00e572049e29f
KHALTI_SECRET_KEY=test_secret_key_26b206e987c94488828bbf13e51d141e
KHALTI_INITIATE_URL=https://a.khalti.com/api/v2/epayment/initiate/
KHALTI_LOOKUP_URL=https://a.khalti.com/api/v2/epayment/lookup/

# Loyalty Program
LOYALTY_POINTS_PER_HUNDRED=10
LOYALTY_POINT_REDEEM_VALUE=1.0
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Seed Initial Data (Admin, Customer, Coffee Menu)

A custom Django management command is included to seed all categories, roasts, bakery treats, admin, and demo customer data:

```bash
python manage.py seed_data
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## 🔑 Pre-Configured Demo Accounts

| Account Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Owner / Staff Admin** | `admin` | `admin12345` | `admin@moderncoffee.com` |
| **Coffee Customer** | `barista_john` | `coffee12345` | `john@example.com` |

---

## 💳 Payment Gateway: Khalti Sandbox Flow

1. Customer proceeds to checkout with items in cart.
2. Selects **Pay with Khalti**.
3. Backend calls Khalti v2 ePayment initiation API (`https://a.khalti.com/api/v2/epayment/initiate/`) passing secret key from `.env`.
4. Customer completes the test payment in the sandbox portal.
5. Khalti redirects to `payments:khalti_verify` with `pidx`, `status`, and `purchase_order_id`.
6. Django backend calls Khalti `lookup/` API to verify payment integrity before marking the order as `PAID`.
7. Once verified:
   - Order payment status becomes `PAID`
   - Order status becomes `CONFIRMED`
   - Transaction ID is recorded
   - Customer is credited with loyalty points (10 points per Rs. 100 spent)
   - Cart is cleared
   - Customer receives the confirmation receipt.

---

## 🧪 Running the Automated Test Suite

The project includes unit and integration tests covering authentication, catalog, shopping cart, checkout, Khalti verification, loyalty calculations, and object-level authorization:

```bash
python manage.py test
```

Expected output:
```text
Ran 19 tests in ~20s
OK
```

---

## 🐘 Migrating from SQLite to PostgreSQL

To deploy this project to production with PostgreSQL:

1. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```
2. Update `.env`:
   ```env
   DATABASE_ENGINE=django.db.backends.postgresql
   DATABASE_NAME=modern_coffee_db
   DATABASE_USER=your_postgres_user
   DATABASE_PASSWORD=your_postgres_password
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   ```
3. Update `config/settings.py` (already designed to load DB configuration dynamically from environment variables).
4. Run migrations:
   ```bash
   python manage.py migrate
   ```

---

## 📜 License
Developed for educational, portfolio, and commercial coffee ordering demonstration. All rights reserved.
