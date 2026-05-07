# Executive Coach Builders — Web Application

A Django-based web application for Executive Coach Builders, providing internal tools for managing leads and employee accounts, public site content, optional AI/LLM features, and sales email (SMTP/IMAP).

---
## Dev Admin Account

#### Username: test_user
#### Password: Test123!

## Prerequisites

Before setting up the project, make sure you have the following installed:

- **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/GabrielConner/ExecutiveCoachBuilders.git
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
pip install -r requirements.txt
```

### 4. Navigate to the Django Project

```bash
cd ecb_website
```

### 5. Environment variables *(optional but recommended)*

Copy the example file and edit as needed (same folder as `manage.py`):

```bash
cp .env.example .env
```

Typical entries: `SECRET_KEY`, `DEBUG`, `DATABASE_URL` (Postgres in production; omit for local SQLite), LLM API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.), and mail settings (`SMTP_*`, `IMAP_*`) if not using only the in-app Settings UI. The app loads `.env` automatically when [python-dotenv](https://github.com/theskumar/python-dotenv) is installed.

### 6. Apply Database Migrations *(WHEN READY)*

```bash
python manage.py migrate
```

This creates the SQLite database (`db.sqlite3`) when `DATABASE_URL` is unset, and applies all schema migrations.

### 7. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password. This account will have full access to the Django admin panel.

### 8. Run the Development Server

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
├── requirements.txt             # Python dependencies
└── ecb_website/
    ├── manage.py                # Django management utility
    ├── .env.example             # Env template (copy to .env; .env is not committed)
    ├── db.sqlite3               # SQLite database (auto-generated; dev default)
    ├── account/                 # Staff portal, auth (Employee)
    ├── leads/                   # CRM leads & timeline
    ├── agent/                   # LLM settings & in-portal AI usage
    ├── emailing/                # SMTP/IMAP integration
    ├── blog/, client_view/, garage/, edit_site/  # Public site & CMS
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

Pinned in `requirements.txt` (run `pip freeze` locally for the full resolved set). Main packages:

| Package        | Version (pinned) |
|----------------|------------------|
| Django         | 6.0.3            |
| django-taggit  | 6.1.0            |
| Pillow         | 11.2.1           |
| python-dotenv  | 1.0.1            |
| psycopg        | 3.2.9 (binary)   | *optional; for PostgreSQL* |

---

## Notes

- **Database:** Default development database is **SQLite** (`ecb_website/db.sqlite3`). For **PostgreSQL**, set `DATABASE_URL` in `.env` (see `ecb_website/settings.py`), install deps, then `migrate`.
- **Production:** Set `DEBUG=0`, a strong `SECRET_KEY` in `.env`, correct `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`, run `collectstatic` (set `STATIC_ROOT`), and serve user uploads from `MEDIA_ROOT` (defaults under `ecb_website/media/` or override via env). Use a reverse proxy (e.g. nginx) in front of the app server.
- **Secrets:** Prefer `.env` or the host environment; do not commit `.env`. Values saved in the admin/portal (e.g. AI keys, email passwords in Email Settings) are stored in the database and override env fallbacks where applicable.
- For local development, `DEBUG` defaults to on unless overridden in `.env`.
