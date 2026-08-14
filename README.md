# 🛒 Django E-Commerce Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.x-red?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A role-based e-commerce application featuring distinct **Buyer** and **Seller** workflows, RESTful APIs, and full administrative capabilities built using **Python, Django, Django REST Framework, and PostgreSQL/SQLite**.

---

## 📌 Table of Contents

- [Features](#-features)
  - [Buyer Capabilities](#buyer)
  - [Seller Capabilities](#seller)
  - [Admin & API](#admin--api)
- [Tech Stack](#%EF%B8%8F-tech-stack)
- [User Workflows](#-user-workflows)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Admin Access & Demo Credentials](#-admin-access--demo-credentials)
- [Running Tests](#-running-tests)
- [Project Goals](#-project-goals)
- [Author](#-author)

---

## ✨ Features

### 🛍️ Buyer
* **Account Management:** User registration and secure login.
* **Product Discovery:** Browse catalog and inspect detailed product specifications.
* **Cart System:** Add items, modify quantities, and remove products seamlessly.
* **Order Processing:** Place orders and track comprehensive order history.
* **Feedback:** Submit reviews and ratings for purchased products.

### 🏪 Seller
* **Seller Dashboard:** High-level overview of listed items and incoming orders.
* **Product Catalog Control:** Full CRUD functionality (Add, Edit, Update, Delete) for inventory.
* **Order Management:** View and update fulfillment statuses for buyer orders.

### ⚙️ Admin & API
* **Django Admin Integration:** Complete backend user and system data control.
* **RESTful Architecture:** Clean REST API endpoints built with **Django REST Framework (DRF)**.
* **Access Control:** Role-Based Access Control (RBAC) securing endpoints based on user permissions.

---

## 🛠️ Tech Stack

| Category | Technology |
| :--- | :--- |
| **Language** | Python |
| **Backend Framework** | Django, Django REST Framework (DRF) |
| **Database** | SQLite (Development) / PostgreSQL (Production) |
| **Frontend UI** | HTML5, CSS3, Bootstrap |
| **Version Control** | Git & GitHub |

---

## 🔄 User Workflows

### 🛍️ Buyer Flow
```text
Register/Login
      │
      ▼
Browse Products ──► View Details
      │
      ▼
 Add to Cart
      │
      ▼
 Place Order ──► View Order History ──► Add Product Review
```

### 🏪 Seller Flow
```text
Login as Seller
      │
      ▼
Seller Dashboard
      │
 ┌────┴────────────────────────┐
 ▼                             ▼
Manage Inventory           Manage Orders
(Add / Edit / Delete)    (View & Update Status)
```

---

## 📁 Project Structure

```text
django-ecommerce-platform/
│
├── manage.py
├── requirements.txt
├── run_project.bat          # Automated Windows setup script
├── README.md
│
├── core/                    # Core project configuration & settings
├── apps/                    # Django apps (accounts, products, orders, cart, api)
├── templates/               # HTML templates
├── static/                  # CSS, JS, and UI assets
├── media/                   # User-uploaded product images
└── database/                # SQLite DB (local dev)
```

---

## 🚀 Getting Started

An automated Windows batch script (`run_project.bat`) is included to set up the virtual environment, install dependencies, run migrations, seed demo accounts, and launch the dev server automatically.

### 1. Clone the Repository
```bash
git clone https://github.com/abhishekc8205/django-ecommerce-platform.git
cd django-ecommerce-platform
```

### 2. Run Automated Setup

**Option A: Windows Command Prompt / File Explorer**
> Double-click `run_project.bat`

**Option B: Windows PowerShell**
```powershell
.\run_project.bat
```

> **What `run_project.bat` does under the hood:**
> 1. Creates virtual environment (`venv`)
> 2. Activates the virtual environment
> 3. Installs `requirements.txt`
> 4. Applies database migrations (`python manage.py migrate`)
> 5. Creates demo admin superuser
> 6. Launches local development server

### 3. Access the Application

Once started, open your browser at:
```text
http://127.0.0.1:8000/
```

---

## 🔐 Admin Access & Demo Credentials

An administrator account is pre-configured for demonstration and testing purposes.

| Field | Credential |
| :--- | :--- |
| **Admin Panel URL** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |
| **Username** | `admin` |
| **Email** | `admin@gmail.com` |
| **Password** | `12345` |

> ⚠️ **Note:** These default credentials are strictly for demonstration and development purposes. Do **not** use default credentials in production settings.

---

## 🧪 Running Tests

Execute the automated test suite via Django's test runner:

```bash
python manage.py test
```

---

## 🎯 Project Purpose

This project highlights end-to-end backend and full-stack implementation including:
- Clean RESTful API design using DRF.
- Explicit database schema structuring and ORM query optimization.
- Custom authentication flows and Role-Based Access Control (RBAC).
- Modular Django architecture and maintainable project organization.

---

## 👨‍💻 Author

**Abhishek Chikhale**
* GitHub: [@abhishekc8205](https://github.com/abhishekc8205)