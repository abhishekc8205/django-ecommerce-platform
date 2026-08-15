# Django E-Commerce Store

A small e-commerce project built with Django. It has separate buyer and seller features, a shopping cart, orders, reviews, and a REST API.

## What it includes

- Register and log in as a buyer or seller
- Browse products and view product details
- Add products to a cart and place orders
- Leave product reviews
- Seller dashboard for managing products, stock, variants, images, and orders
- Django admin panel
- REST API for products and categories

## Built with

- Python
- Django
- Django REST Framework
- SQLite for local development
- Stripe for online payments

## Run the project

You need Python 3.10 or later installed.

### Quick start for Windows

Run this one command from the project folder:

```powershell
.\run_project.bat
```

On the first run, it creates and activates `venv`, installs the required packages, applies database migrations, creates the local admin account if needed, and starts the server. Later runs reuse the same environment.

Then open <http://127.0.0.1:8000/>.

### Manual setup

```bash
git clone https://github.com/abhishekc8205/django-ecommerce-platform.git
cd django-ecommerce-platform
python -m venv venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source venv/bin/activate
```

Install the packages and start the app:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

## Admin login

Open <http://127.0.0.1:8000/admin/>.

When you use `run_project.bat`, the local admin account is:

| Username | Password |
| --- | --- |
| `admin` | `12345` |

Use a different password before deploying the project anywhere public.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/categories/` | List categories |
| GET, POST | `/api/products/` | List products or create one as a seller |
| GET, PUT, PATCH, DELETE | `/api/products/<id>/` | View or manage a product |
| GET | `/api/products/<id>/variants/` | List product variants |
| GET | `/api/products/<id>/images/` | List product images |
| GET | `/api/products/<id>/reviews/` | List product reviews |
| POST | `/api/token/` | Get a JWT access token |
| POST | `/api/token/refresh/` | Refresh a JWT token |

## Useful commands

```bash
# Create database migrations after changing models
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create your own admin user
python manage.py createsuperuser

# Run tests
python manage.py test
```

## Payments

For Stripe checkout, create a `.env` file using `.env.template` as a guide and add your Stripe test keys. Never commit real secret keys.

## Project folders

```text
accounts/  user registration and authentication
project/   Django settings and main URLs
store/     products, cart, orders, reviews, API, and templates
```
