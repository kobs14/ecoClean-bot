# EcoClean Bot

A full-stack **employee management system** designed for small service businesses, featuring a **Telegram bot interface** for field workers and a **REST API** backend. Built with Python, Flask, PostgreSQL, and Docker.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)

---

## Overview

EcoClean Bot solves a common problem for small businesses: managing field employees efficiently. Instead of using complex enterprise software, employees interact with a simple Telegram bot to submit job reports, while managers get real-time summaries and analytics through the API.

### Key Capabilities

- **Account Management** - Create and manage employee accounts with role-based access
- **Telegram Bot Integration** - Employees link their Telegram accounts and submit reports via chat
- **Job Reporting** - Capture job details including location (GPS), payment info, and photos
- **Manager Analytics** - Generate summaries by date range, employee performance, and revenue
- **Email Verification** - Automated verification flow with Telegram bot linking
- **Multi-Environment Support** - Separate configs for development, testing, and production

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram      │────▶│   Bot Service   │────▶│   Flask API     │
│   (Employees)   │     │   (python-      │     │   (REST)        │
│                 │◀────│   telegram-bot) │◀────│                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   PostgreSQL    │
                                                │   Database      │
                                                └─────────────────┘
```

**Three Docker services** communicate via REST APIs and share a PostgreSQL database:
- **api** - Flask backend handling all business logic
- **bot** - Telegram bot for employee interactions
- **db** - PostgreSQL with automatic schema initialization

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend API | Flask (Python 3.10+) | RESTful endpoints, business logic |
| Database | PostgreSQL 15 | Relational data storage |
| Bot | python-telegram-bot | Telegram client interface |
| Auth | bcrypt | Password hashing |
| Storage | Local filesystem (S3-ready) | Photo uploads |
| Containerization | Docker Compose | Multi-service orchestration |
| Testing | pytest + pytest-cov | Automated test suite |

---

## Features

### For Employees (Telegram Bot)

| Feature | Description |
|---------|-------------|
| **Job Reports** | Submit jobs with description, client info, payment details, and photos |
| **Location Tracking** | Automatic GPS coordinates capture |
| **Payment Methods** | Support for Cash, Check, Card, Venmo, PayPal, CashApp, Bank Transfer |
| **Material Requests** | Request supplies and materials |
| **Status Updates** | Update work status in real-time |

### For Managers (API)

| Feature | Description |
|---------|-------------|
| **Account Management** | Full CRUD operations for employee accounts |
| **Role-Based Access** | Admin-only endpoints with decorator-based protection |
| **Reports & Analytics** | Summaries by date range, top performers, revenue breakdown |
| **Email Service** | Verification emails with Telegram linking |
| **Search & Filter** | Find accounts by username, phone, or status |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### 1. Clone and Configure

```bash
git clone https://github.com/kobs14/ecoclean-bot.git
cd ecoclean-bot
```

Create a `.env` file with the following variables:

```env
# Database
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=ecoclean
POSTGRES_DB_TEST=ecoclean_test

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BACKEND_API_URL=http://api:5000

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

### 2. Start Services

```bash
# Development
docker-compose up --build

# Production (detached)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### 3. Access

- **API**: http://localhost:5000
- **Database**: postgresql://localhost:5432
- **Bot**: Running and connected to Telegram

---

## API Endpoints

### Account Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/account/register` | Create new employee account |
| GET | `/account/all` | List all accounts |
| GET | `/account/<id>` | Get account by ID |
| PATCH | `/account/<id>` | Update account fields |
| PUT | `/account/<id>/status` | Toggle active/disabled |
| DELETE | `/account/<id>` | Delete account |
| GET | `/account/accounts/search` | Search accounts |

### Telegram Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/telegram/link` | Link Telegram account with token |

### Job Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/job-report/` | Submit new job report |
| GET | `/job-report/` | List all reports |
| GET | `/job-report/<id>` | Get report by ID |
| GET | `/job-report/account/<id>` | Get reports by employee |
| POST | `/job-report/<id>/photo` | Attach photo to report |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports-summary/` | Generate summary report |

Full API documentation: [docs/API.md](./docs/API.md)

---

## Testing

```bash
# Run all tests
docker-compose --profile test up test --build

# Run with coverage
docker-compose --profile test run test pytest --cov=app app/tests/

# Run specific test file
docker-compose --profile test run test pytest app/tests/test_account/ -v
```

---

## Project Structure

```
ecoclean-bot/
├── app/                      # Flask Backend API
│   ├── main.py               # App factory & blueprints
│   ├── config.py             # Configuration classes
│   ├── auth/                 # Authentication decorators
│   ├── routes/               # API endpoints
│   │   ├── account/          # Account management
│   │   ├── telegram/         # Telegram linking
│   │   ├── job_report/       # Job submissions
│   │   └── reports_summary/  # Analytics
│   ├── storage/              # File storage abstraction
│   │   ├── storage_interface.py
│   │   ├── local_storage.py
│   │   └── s3_storage.py     # S3 ready
│   ├── tests/                # Test suite
│   ├── requirements.txt
│   └── Dockerfile
│
├── bot/                      # Telegram Bot
│   ├── bot.py                # Bot initialization
│   ├── handlers/
│   │   ├── core/             # /start, /menu commands
│   │   ├── employee/         # Job report, estimates, materials
│   │   └── admin/            # Reports, metrics, team management
│   ├── requirements.txt
│   └── Dockerfile
│
├── initdb/                   # Database initialization
│   ├── 00-enable-extensions.sql
│   ├── 01-create-multiple-postgresql-databases.sh
│   └── 02-create-tables.sql
│
├── docs/                     # API documentation
├── docker-compose.yml        # Development config
├── docker-compose.prod.yml   # Production overrides
└── docker-compose.test.yml   # Test environment
```

---

## Database Schema

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   account    │────▶│    email     │     │   telegram   │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (UUID)    │     │ account_id   │     │ account_id   │
│ username     │     │ email_addr   │     │ tg_user_id   │
│ fullname     │     │ verified     │     │ tg_username  │
│ phone        │     │ token        │     │ verified     │
│ password_hash│     └──────────────┘     │ is_admin     │
│ is_admin     │                          └──────────────┘
│ commission   │
│ status       │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  job_report  │────▶│report_photos │
├──────────────┤     ├──────────────┤
│ id (UUID)    │     │ job_report_id│
│ account_id   │     │ photo_url    │
│ latitude     │     │ file_name    │
│ longitude    │     │ file_size    │
│ amount       │     └──────────────┘
│ payment_type │
│ description  │
│ client_info  │
│ status       │
└──────────────┘
```

---

## Development

### Debug Mode

The Flask app runs in debug mode during development. Code changes in `app/` are automatically reflected via volume mounting.

### Adding New Bot Handlers

1. Create handler in `bot/handlers/employee/` or `bot/handlers/admin/`
2. Use `ConversationHandler` for multi-step workflows
3. Register in `bot/bot.py`

### Storage Layer

The storage system uses an abstract interface pattern. To switch to S3:

1. Update `STORAGE_TYPE` in `config.py` to `'s3'`
2. Add AWS credentials to `STORAGE_CONFIG`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker fails to start | Ensure Docker is running, check `.env` file |
| Database connection error | Wait for healthcheck, verify credentials |
| Bot not responding | Check `TELEGRAM_BOT_TOKEN` is valid |
| Tests fail | Run `docker-compose down -v` to reset volumes |

---

## Contact

- **Email**: yacob.k.dev@gmail.com
- **GitHub**: [Open an Issue](https://github.com/kobs14/ecoclean-bot/issues)
- **LinkedIn**: [Kobe Horshid](https://www.linkedin.com/in/kobe-horshid-965031217)

---

## License

See the [LICENSE](./LICENSE) file for details.
