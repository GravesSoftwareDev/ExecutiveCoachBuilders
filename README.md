# Executive Coach Builders — Web Application

A Django-based web application for Executive Coach Builders (ECB), providing a public-facing website, a staff CRM portal, optional AI/LLM features, and sales email (SMTP/IMAP) integration.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation & Setup](#installation--setup)
3. [Environment Variables](#environment-variables)
4. [Running the Application](#running-the-application)
5. [Project Structure](#project-structure)
6. [User Guide](#user-guide)
   - [Public Website](#public-website)
   - [Staff Portal](#staff-portal)
   - [CRM — Leads](#crm--leads)
   - [AI Agent](#ai-agent)
   - [Email Integration](#email-integration)
   - [Fleet Management](#fleet-management)
   - [Blog / News](#blog--news)
   - [Site & Team Management](#site--team-management)
   - [User Management](#user-management)
7. [Data Models](#data-models)
8. [Dependencies](#dependencies)
9. [Production Notes](#production-notes)

---

## Prerequisites

- **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)
- *(Optional)* **PostgreSQL** — for production use. SQLite is the default for local development.

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/GabrielConner/ExecutiveCoachBuilders.git
cd ExecutiveCoachBuilders
```

### 2. Create and Activate a Virtual Environment

From the repository root:

```bash
python3 -m venv venv
```

Activate:

- **macOS / Linux:**
  ```bash
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

> **Tip (macOS/Linux):** If activation fails, try `rm -rf venv && python3 -m venv venv && source venv/bin/activate`.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Navigate to the Django Project

All remaining commands run from the `ecb_website/` directory:

```bash
cd ecb_website
```

### 5. Configure Environment Variables

Copy the example environment file and edit it as needed:

```bash
cp .env.example .env
```

At minimum, set a strong `SECRET_KEY`. See [Environment Variables](#environment-variables) for full details.

### 6. Apply Database Migrations

```bash
python manage.py migrate
```

This creates `db.sqlite3` (the default SQLite database) and applies all schema migrations.

### 7. Create a Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts. This account gains full access to both the Django admin panel and the staff portal with Admin-level role.

### 8. (Optional) Load a Dev Fixture

A pre-built dev admin account is included for quick testing:

| Username    | Password  |
|-------------|-----------|
| `test_user` | `Test123!` |

---

## Environment Variables

The application reads from `ecb_website/.env` (loaded automatically via `python-dotenv`). Never commit this file. A template is provided at `ecb_website/.env.example`.

### Django Core

| Variable              | Default                              | Description |
|-----------------------|--------------------------------------|-------------|
| `SECRET_KEY`          | `change-me`                          | Django secret key — change this before any deployment |
| `DEBUG`               | `1`                                  | `1` = development mode; set `0` in production |
| `ALLOWED_HOSTS`       | `127.0.0.1,localhost`                | Comma-separated list of valid hostnames |
| `CSRF_TRUSTED_ORIGINS`| `http://127.0.0.1:8000,...`          | Required for form submissions in production |

### Database

| Variable       | Default | Description |
|----------------|---------|-------------|
| `DATABASE_URL` | *(unset)* | Leave unset to use SQLite. Set to a PostgreSQL URL for production, e.g. `postgresql://user:pass@host:5432/dbname` |

### LLM / AI Agent

> These can also be configured (and will be overridden) by the **Settings → AI Agent** page inside the staff portal.

| Variable           | Default                        | Description |
|--------------------|--------------------------------|-------------|
| `LLM_PROVIDER`     | `openai`                       | Active provider: `openai`, `gemini`, `deepseek`, or `openrouter` |
| `OPENAI_API_KEY`   | *(empty)*                      | OpenAI API key |
| `OPENAI_MODEL`     | `gpt-4o-mini`                  | Model to use |
| `GEMINI_API_KEY`   | *(empty)*                      | Google Gemini API key |
| `GEMINI_MODEL`     | `gemini-2.0-flash`             | Model to use |
| `DEEPSEEK_API_KEY` | *(empty)*                      | DeepSeek API key |
| `DEEPSEEK_MODEL`   | `deepseek-chat`                | Model to use |
| `OPENROUTER_API_KEY` | *(empty)*                    | OpenRouter API key |
| `OPENROUTER_MODEL` | `anthropic/claude-3.5-sonnet`  | Model to use |

### Outbound Email (SMTP)

| Variable          | Default          | Description |
|-------------------|------------------|-------------|
| `SMTP_ENABLED`    | `0`              | Set to `1` to enable outbound email |
| `SMTP_HOST`       | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT`       | `587`            | SMTP port |
| `SMTP_USERNAME`   | *(empty)*        | SMTP login username |
| `SMTP_PASSWORD`   | *(empty)*        | SMTP login password (use an app password for Gmail) |
| `SMTP_USE_TLS`    | `1`              | `1` = enable STARTTLS |
| `SMTP_FROM_ADDRESS` | *(empty)*      | From address for outgoing mail |
| `SMTP_FROM_NAME`  | *(empty)*        | Display name for outgoing mail |

### Inbound Email (IMAP)

| Variable          | Default           | Description |
|-------------------|-------------------|-------------|
| `IMAP_ENABLED`    | `0`               | Set to `1` to enable inbox polling |
| `IMAP_HOST`       | `imap.gmail.com`  | IMAP server hostname |
| `IMAP_PORT`       | `993`             | IMAP port |
| `IMAP_USERNAME`   | *(empty)*         | IMAP login username |
| `IMAP_PASSWORD`   | *(empty)*         | IMAP login password |
| `IMAP_USE_SSL`    | `1`               | `1` = use SSL |
| `IMAP_FOLDER`     | `INBOX`           | Mailbox folder to poll |
| `EMAIL_INTERNAL_DOMAINS` | `ecblimo.com` | Comma-separated internal domain(s); used to skip internal senders |

### File Storage *(optional)*

| Variable     | Default                    | Description |
|--------------|----------------------------|-------------|
| `MEDIA_ROOT` | `ecb_website/media/`       | Override where uploaded files are stored |
| `STATIC_ROOT`| *(unset)*                  | Set for `collectstatic` in production |

---

## Running the Application

```bash
# From ecb_website/
python manage.py runserver
```

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/` | Public website |
| `http://127.0.0.1:8000/portal/` | Staff portal (login required) |
| `http://127.0.0.1:8000/admin/` | Django admin panel (superuser required) |

---

## Project Structure

```
ExecutiveCoachBuilders/
├── venv/                        # Virtual environment (not committed)
├── requirements.txt             # Python dependencies
└── ecb_website/
    ├── manage.py                # Django management utility
    ├── .env.example             # Environment variable template
    ├── db.sqlite3               # SQLite database (auto-generated; dev default)
    ├── media/                   # Uploaded files (blog, vehicles, team, site settings)
    ├── static/                  # CSS, JS, images
    ├── account/                 # Staff portal authentication & employee model
    ├── leads/                   # CRM — lead tracking and chat sessions
    ├── agent/                   # AI/LLM configuration and call logging
    ├── emailing/                # SMTP/IMAP email integration
    ├── blog/                    # Blog/news article management
    ├── garage/                  # Fleet/vehicle management (portal-side)
    ├── edit_site/               # Admin controls for public site content
    ├── client_view/             # Public-facing website and visitor chat
    └── ecb_website/             # Project configuration
        ├── settings.py
        ├── urls.py
        ├── wsgi.py
        └── asgi.py
```

---

## User Guide

### Public Website

The public site is accessible without logging in at `http://127.0.0.1:8000/`.

| Page | Description |
|------|-------------|
| **Home** | Landing page with company overview, services, and call-to-action |
| **Fleet** | Catalog of available vehicles (Bus, Coach, Sprinter, RV, Custom) with hero images |
| **About** | Company background and team member profiles |
| **Blog / News** | Published articles and company news |
| **Contact** | Contact form — submissions are automatically saved as Leads in the CRM |
| **Visitor Chat** | AI-powered chat widget on the public site that answers questions about ECB |

---

### Staff Portal

Log in at `/portal/login/`. Staff are either **Agents** or **Admins**.

| Role  | Capabilities |
|-------|-------------|
| **Agent** | View and manage leads assigned to them; access AI chat features |
| **Admin** | Everything an Agent can do, plus manage users, site content, fleet, blog, and settings |

Admins can also grant granular permissions per employee:

| Permission | Controls |
|------------|----------|
| `can_edit_site` | About page, services, contact info |
| `can_edit_fleet` | Vehicle listings |
| `can_edit_blog` | Blog articles |
| `can_edit_services` | Service descriptions |
| `can_edit_team` | Team member profiles |

---

### CRM — Leads

Navigate to **Portal → Leads**.

**Lead pipeline stages:**

| Stage | Description |
|-------|-------------|
| New | Freshly submitted; not yet reviewed |
| In Progress | Actively being worked |
| Closed | Sale completed or contact ended |

**Lead fields:**

| Field | Description |
|-------|-------------|
| Name / Email / Phone | Contact info |
| Company | Optional company name |
| Budget | Estimated budget |
| Interest | Vehicle type: Bus, Coach, Sprinter, or Custom |
| Use Case | Intended use of the vehicle |
| Timeline | Purchase timeframe |
| Passengers | Estimated passenger count |
| Source | How the lead was acquired |
| Priority | Normal or High |
| Hot Lead | Flag with a reason if immediate follow-up is needed |
| Assigned To | Staff member responsible |

**AI enrichment:** When an API key is configured, the AI Agent can analyze a lead and populate structured notes (`ai_structured`) automatically.

**Lead chat:** Each lead has an attached chat thread where staff can ask the AI questions about the lead in context.

---

### AI Agent

Navigate to **Portal → Settings → AI Agent** (Admin only).

Configure the LLM provider and model, set a daily call quota per user, and review the call log for observability. Supported providers:

- **OpenAI** (default: `gpt-4o-mini`)
- **Google Gemini** (default: `gemini-2.0-flash`)
- **DeepSeek** (default: `deepseek-chat`)
- **OpenRouter** (default: `anthropic/claude-3.5-sonnet`)

The AI is used for:

- Lead enrichment and AI-structured notes
- In-portal chat about individual leads
- Blog draft assistance
- Email triage (matching incoming emails to leads)
- Public website visitor chat

> Settings saved in the portal's UI override the `.env` fallback values.

---

### Email Integration

Navigate to **Portal → Settings → Sales Email** (Admin only).

**Outbound (SMTP):**
- Send emails to leads directly from the portal
- Auto-appends a configurable email signature
- Supports TLS (Gmail, Outlook, or any SMTP server)

**Inbound (IMAP):**
- Polls the configured inbox for new messages
- De-duplicates by `Message-ID` header
- Stores incoming emails as an audit log
- AI triage can match emails to existing leads automatically
- Internal senders (matching `EMAIL_INTERNAL_DOMAINS`) are filtered out

> For Gmail: enable two-factor authentication and use an [App Password](https://support.google.com/accounts/answer/185833) instead of your account password.

---

### Fleet Management

Navigate to **Portal → Fleet** (requires `can_edit_fleet`).

- Add, edit, and remove vehicles
- Upload hero images per vehicle
- Set display ordering for the public catalog
- Vehicle types: Bus, Coach, Sprinter, RV, Custom

---

### Blog / News

Navigate to **Portal → Blog** (requires `can_edit_blog`).

- Create and edit articles with markdown support
- Tag articles with keywords (powered by `django-taggit`)
- Set status to **Draft** or **Published**
- Upload images and videos per article
- Use the AI assistant to help draft article content

Only **Published** articles appear on the public site.

---

### Site & Team Management

Navigate to **Portal → Settings → Site** (requires `can_edit_site` / `can_edit_team`).

- Edit the About page content
- Manage team member profiles (name, photo, role)
- Update service descriptions and icons
- Change contact information (phone, address, social media)
- Customize the site's color scheme and theme (including dark mode)

---

### User Management

Navigate to **Portal → Users** (Admin only).

- Create new employee accounts
- Assign roles (Agent / Admin)
- Grant or revoke granular permissions
- Deactivate accounts without deleting them

---

## Data Models

### Employee

Extends Django's `AbstractUser`. Each employee is assigned one of two roles:

| Role  | Description |
|-------|-------------|
| Agent | Standard user; manages their assigned leads |
| Admin | Elevated access; manages users, settings, and all content |

### Lead

| Field         | Description |
|---------------|-------------|
| `first_name`  | Lead's first name |
| `last_name`   | Lead's last name |
| `email`       | Contact email address |
| `phone_number`| Contact phone (validated format) |
| `company`     | Company name (optional) |
| `budget`      | Estimated budget |
| `interest`    | Vehicle type: Bus, Coach, Sprinter, or Custom |
| `use_case`    | Intended use |
| `timeline`    | Purchase timeframe |
| `passengers`  | Estimated passenger count |
| `source`      | How the lead originated |
| `stage`       | Pipeline stage: new / in_progress / closed |
| `priority`    | Normal or High |
| `hot_lead`    | Boolean flag |
| `hot_reason`  | Explanation for hot lead flag |
| `assigned_to` | FK → Employee |
| `ai_structured` | JSON field populated by AI enrichment |

---

## Dependencies

| Package         | Version  | Purpose |
|-----------------|----------|---------|
| Django          | 6.0.3    | Web framework |
| django-taggit   | 6.1.0    | Blog article tagging |
| Pillow          | 11.2.1   | Image uploads |
| python-dotenv   | 1.0.1    | `.env` file loading |
| psycopg (binary)| 3.2.9    | PostgreSQL driver *(optional)* |

---

## Production Notes

- **Secret key:** Generate a new random `SECRET_KEY` and set it in `.env`. Never use the placeholder.
- **Debug mode:** Set `DEBUG=0`. Django will serve no static files in this mode — use a web server (e.g. nginx) instead.
- **Allowed hosts:** Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your actual domain(s).
- **Static files:** Run `python manage.py collectstatic` and set `STATIC_ROOT` in `.env`. Serve the collected files via nginx or a CDN.
- **Media files:** Set `MEDIA_ROOT` to a persistent directory and serve it via nginx.
- **Database:** Set `DATABASE_URL` to a PostgreSQL connection string. SQLite is not recommended for multi-user production workloads.
- **Reverse proxy:** Run `gunicorn ecb_website.wsgi` behind nginx or a similar proxy in production.
- **Secrets:** API keys and email passwords entered in the portal Settings UI are stored in the database. Restrict database access accordingly.
