# Executive Coach Builders — Web Application

A Django-based web application for Executive Coach Builders, providing internal tools for managing leads and employee accounts.

---

## Prerequisites

Before setting up the project, make sure you have the following installed:

- **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <https://github.com/GabrielConner/ExecutiveCoachBuilders.git>
cd ExecutiveCoachBuilders
```

### 2. Create and Activate a Virtual Environment

From the root of the cloned repository:

```bash
python3 -m venv venv
```

Activate the virtual environment:

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
##### If this doesn't work try
- **macOS/ Linux:**
  ```bash
  rm -rf venv                    
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```

You should see `(venv)` in your terminal prompt once activated.

### 3. Install Dependencies

```bash
pip install -r ecb_website/requirements.txt
```

### 4. Navigate to the Django Project

```bash
cd ecb_website
```

### 5. Apply Database Migrations *(WHEN READY)*

```bash
python manage.py migrate
```

This creates the SQLite database (`db.sqlite3`) and applies all schema migrations, including the custom `Employee` and `Lead` models.

### 6. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password. This account will have full access to the Django admin panel.

### 7. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at **http://127.0.0.1:8000/**

The Django admin panel is available at **http://127.0.0.1:8000/admin/**

---

## Project Structure

```
ExecutiveCoachBuilders/
├── venv/                        # Virtual environment (not committed)
└── ecb_website/
    ├── manage.py                # Django management utility
    ├── requirements.txt         # Python dependencies
    ├── db.sqlite3               # SQLite database (auto-generated)
    ├── account/                 # Account app (employees & leads)
    │   ├── models.py            # Employee and Lead data models
    │   ├── views.py
    │   ├── admin.py
    │   └── migrations/
    └── ecb_website/             # Project configuration
        ├── settings.py
        ├── urls.py
        ├── wsgi.py
        └── asgi.py
```

---

## Data Models

### Employee
Extends Django's built-in `AbstractUser`. Each employee is assigned one of two roles:

| Role  | Description                        |
|-------|------------------------------------|
| Agent | Standard user; manages leads       |
| Admin | Elevated access; manages all users |

### Lead
Represents a prospective customer. Tracks the following:

| Field        | Description                                   |
|--------------|-----------------------------------------------|
| first_name   | Lead's first name                             |
| last_name    | Lead's last name                              |
| email        | Contact email address                         |
| phone_number | Contact phone number                          |
| company      | Company name (optional)                       |
| budget       | Estimated budget                              |
| interest     | Vehicle interest: Bus, Coach, Sprinter, or Custom |

---

## Dependencies

| Package   | Version |
|-----------|---------|
| Django    | 6.0.4   |
| asgiref   | 3.11.1  |
| sqlparse  | 0.5.5   |

---

## Notes

- The default database is **SQLite**, stored locally as `db.sqlite3`. No additional database setup is required for development.
- `DEBUG = True` is set by default. Do not deploy with this setting enabled in production.
- The `SECRET_KEY` in `settings.py` must be replaced with a secure, private value before any production deployment.
