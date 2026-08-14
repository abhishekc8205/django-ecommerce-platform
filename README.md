# 🛒 Django E-Commerce Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/Django%20REST%20Framework-3.x-red?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A role-based e-commerce application built with **Python, Django, and Django REST Framework (DRF)**.

The application provides separate **Buyer and Seller workflows**, product management, shopping cart functionality, order processing, product reviews, authentication, role-based access control, REST APIs, and Django administration.

---

## 📌 Table of Contents

- [Features](#-features)
  - [Buyer](#-buyer)
  - [Seller](#-seller)
  - [Admin](#-admin)
  - [REST API](#-rest-api)
- [Tech Stack](#️-tech-stack)
- [User Workflows](#-user-workflows)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Admin Access](#-admin-access)
- [Testing](#-testing)
- [Project Purpose](#-project-purpose)
- [Author](#-author)

---

# ✨ Features

## 🛍️ Buyer

- User registration and login
- Browse available products
- View product details
- Add products to cart
- Update cart quantities
- Remove products from cart
- Place orders
- View order history
- Submit product reviews and ratings

---

## 🏪 Seller

- Seller dashboard
- Add new products
- Edit existing products
- Delete products
- Manage product inventory
- View customer orders
- Update order status

---

## 🔐 Admin

- Django Admin Panel
- Manage users
- Manage products
- Manage orders
- Manage reviews and application data
- Full administrative access through Django Admin

---

## 🔗 REST API

The project uses **Django REST Framework** to provide RESTful APIs.

API functionality includes:

- Product APIs
- Category APIs
- Authentication APIs
- CRUD operations
- Role-based permissions
- JWT authentication

---

# 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Programming Language** | Python |
| **Backend Framework** | Django |
| **API Framework** | Django REST Framework |
| **Authentication** | JWT |
| **Database** | SQLite / PostgreSQL |
| **Frontend** | HTML, CSS, Bootstrap |
| **Version Control** | Git & GitHub |

---

# 🔄 User Workflows

## 🛍️ Buyer Flow

```text
Register / Login
       │
       ▼
Browse Products
       │
       ▼
View Product Details
       │
       ▼
Add to Cart
       │
       ▼
Checkout
       │
       ▼
Place Order
       │
       ▼
View Order History
       │
       ▼
Add Product Review

## 🏪 Seller Flow

```text
Login as Seller
       │
       ▼
Seller Dashboard
       │
       ├───────────────┐
       ▼               ▼
Manage Products    Manage Orders
       │               │
       ▼               ▼
Add / Edit /       View / Update
Delete Products    Order Status
```

# 📁 Project Structure

```text
django-ecommerce-platform/
│
├── manage.py
├── requirements.txt
├── run_project.bat
├── README.md
│
├── core/                 # Django project configuration
├── apps/                 # Application modules
│
├── templates/            # HTML templates
├── static/               # CSS, JavaScript and static assets
├── media/                # Uploaded product images
│
└── database/             # Local database/sample data
```

The exact application modules may vary depending on the project implementation.

# 🚀 Getting Started

The project includes a Windows batch file called `run_project.bat` that automates the local development setup.

## Prerequisites

Make sure the following are installed:

* Windows
* Python 3.10 or higher
* Git

The project uses a Python virtual environment, which is automatically created by the setup script.

## 1. Clone the Repository

```bash
git clone https://github.com/abhishekc8205/django-ecommerce-platform.git
```

Move into the project directory:

```bash
cd django-ecommerce-platform
```

## 2. Run the Automated Setup

### Option A — File Explorer

Double-click:

```text
run_project.bat
```

### Option B — PowerShell

Run:

```powershell
.\run_project.bat
```

The script automatically performs the following steps:

```text
Create virtual environment
        ↓
Activate virtual environment
        ↓
Install dependencies
        ↓
Run database migrations
        ↓
Create admin superuser
        ↓
Start Django development server
```

No manual virtual environment setup is required.

## 3. Open the Application

Once the server starts, open:

http://127.0.0.1:8000/

# 🔐 Admin Access

The setup script automatically creates the admin account if it does not already exist.

## Demo Credentials

| Field     | Value                        |
| --------- | ---------------------------- |
| Admin URL | http://127.0.0.1:8000/admin/ |
| Username  | `admin`                      |
| Email     | `admin@gmail.com`            |
| Password  | `12345`                      |

Open the admin panel:

http://127.0.0.1:8000/admin/

Then log in using the credentials above.

> ⚠️ **Note:** These credentials are intended only for local development, demonstrations, and interviews. Do not use them in a production environment.

# 🧪 Testing

Run the Django test suite using:

```bash
python manage.py test
```

Django will automatically discover and execute the project's test cases.

# ⚙️ Useful Django Commands

If you need to work with the project manually:

### Create migrations

```bash
python manage.py makemigrations
```

### Apply migrations

```bash
python manage.py migrate
```

### Create a superuser

```bash
python manage.py createsuperuser
```

### Run the development server

```bash
python manage.py runserver
```

# 🔒 Environment Variables

Sensitive configuration should be stored in environment variables rather than committed to Git.

Use the provided environment template if available:

```text
.env.template
```

Create your local `.env` file and add the required configuration.

`.env` files should not be committed to GitHub.

# 🎯 Project Purpose

This project demonstrates practical backend development using Django and Django REST Framework.

Key concepts demonstrated:

* Django application architecture
* REST API development
* CRUD operations
* Django ORM
* Database relationships
* Authentication
* JWT authentication
* Role-Based Access Control (RBAC)
* Product management
* Shopping cart functionality
* Order processing
* Review and rating functionality
* Django Admin
* Git and GitHub

# 💡 Interview Highlights

The project can be used to demonstrate knowledge of:

## Backend

* Django
* Django REST Framework
* RESTful API design
* Django ORM
* Authentication and authorization
* Role-based permissions

## Database

* Relational database design
* Django models
* Foreign keys
* Database migrations
* CRUD operations

## Development

* Virtual environments
* Dependency management
* Environment variables
* Git version control
* Automated local setup using a Windows batch script

# 👨‍💻 Author

**Abhishek Chikhale**

GitHub: `@abhishekc8205`

# ⭐ Project Repository

`django-ecommerce-platform`

---

# One Thing Before You Push

Your **BAT file needs to actually contain the superuser creation command** if the README says it creates the admin automatically.

The relevant section should be:

```bat
echo.
echo Running database migrations...
python manage.py migrate

echo.
echo Creating admin superuser if it does not exist...
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@gmail.com','12345')"

echo.
echo Starting Django server...
python manage.py runserver 0.0.0.0:8000
```
