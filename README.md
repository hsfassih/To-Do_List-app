# To-Do List API

A production-ready RESTful To-Do List API built with **FastAPI**, featuring JWT authentication, role-based access control, async SQLite persistence, Redis caching, and rate limiting.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)

---

## Getting Started

### Prerequisites

- Python 3.10+
- Redis server running locally (or accessible via URL)

### Installation

```bash
# 1. Clone the repository and navigate into the project folder
cd To-Do_List-app

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up Redis (see Redis Setup with Docker below)
```

### Redis Setup with Docker

The easiest way to run Redis locally is with Docker — no local installation required:

```bash
# Pull and start a Redis container
docker run -d --name redis-local -p 6379:6379 redis:alpine

# Verify it's running
docker ps

# Test the connection
docker exec -it redis-local redis-cli ping
# Expected output: PONG
```

To stop and restart the container between sessions:

```bash
docker stop redis-local
docker start redis-local
```

Make sure your `.env` has:

```env
redis_url=redis://localhost:6379
```

### Database Setup & Migrations

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create an initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations to the database
alembic upgrade head

# To revert to a previous migration
alembic downgrade -1
```

---

## Tech Stack

| Layer | Library |
|---|---|
| Web Framework | `fastapi` |
| ASGI Server | `uvicorn[standard]` |
| ORM / Models | `sqlmodel`, `sqlalchemy[asyncio]` |
| Database Driver | `aiosqlite` |
| Auth (JWT) | `python-jose[cryptography]` |
| Password Hashing | `pwdlib[argon2]` |
| Caching | `fastapi-redis-cache` |
| Rate Limiting | `slowapi` |
| Validation | `pydantic`, `orjson` |
| Migrations | `alembic` |
| Config | `python-dotenv` |

---

## Project Structure

```
To-Do_List-app/
├── .env                        # Environment variables (not committed)
├── .gitignore
├── alembic.ini                 # Alembic configuration
├── alembic/
│   ├── env.py                  # Alembic runtime environment
│   ├── script.py.mako          # Migration file template
│   └── versions/               # Generated migration scripts
│       ├── 515a9705851d_initial_schema.py
│       ├── 39b779c30137_split_names.py
│       ├── 4d3a75790e3c_merge_branches.py
│       ├── 7bfd627ece2f_create_resume_table.py
│       └── a55b1f053acf_create_post_table.py
└── src/
    ├── main.py                 # FastAPI app, lifespan, routers, and all route handlers
    ├── config.py               # Pydantic Settings — loads and validates .env variables
    ├── middleware.py           # RequestLogMiddleware & RequestIDMiddleware
    ├── requirements.txt        # Python dependencies
    ├── auth/
    │   ├── database.py         # Async engine and get_db session dependency
    │   ├── dependancies.py     # get_current_user and require_admin auth guards
    │   ├── schemas.py          # Pydantic request body schemas (Register, Login, UserRequest)
    │   └── utils.py            # JWT creation/verification and password hashing utilities
    ├── seed/
    │   └── initial_data.py     # Hardcoded seed data inserted on first startup
    ├── tasks/
    │   ├── models.py           # Task SQLModel (DB table definition)
    │   ├── repository.py       # TaskRepository — async data access layer
    │   └── service.py          # Task business logic layer
    └── users/
        ├── models.py           # User SQLModel (DB table definition)
        ├── repository.py       # UserRepo — async data access layer
        └── service.py          # User business logic layer
```

