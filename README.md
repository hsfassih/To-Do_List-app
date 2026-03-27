# To-Do List API

A production-ready RESTful To-Do List API built with **FastAPI**, featuring JWT authentication, role-based access control, async SQLite persistence, Redis caching, and rate limiting.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Models](#data-models)
- [API Endpoints](#api-endpoints)
- [Authentication & Authorization](#authentication--authorization)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
- [Database Migrations](#database-migrations)
- [Seeded Data](#seeded-data)

---

## Features

- **JWT Authentication** — Secure Bearer token login and registration
- **Role-Based Access Control** — `admin` and `user` roles with protected endpoints
- **Async Database** — Non-blocking SQLite via `aiosqlite` and SQLAlchemy async engine
- **Repository Pattern** — Clean separation of data access logic from route handlers
- **Redis Caching** — Task list responses cached for 30 seconds to reduce DB load
- **Rate Limiting** — User listing endpoint restricted to 5 requests/minute per IP
- **Auto DB Initialization** — Tables and seed data are created automatically on first startup
- **Alembic Migrations** — Schema version control for incremental database changes
- **Password Hashing** — Passwords are hashed using Argon2 via `pwdlib`

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
├── main.py             # FastAPI app, lifespan, and all route handlers
├── Authx2.py           # JWT creation/verification, password utilities, auth dependencies
├── users.py            # User SQLModel (DB table definition)
├── tasks.py            # Task SQLModel (DB table definition)
├── user_repo.py        # UserRepo — async data access layer for users
├── task_repo.py        # TaskRepository — async data access layer for tasks
├── request_utils.py    # Pydantic request body schemas
├── initial_data.py     # Hardcoded seed data (users & tasks)
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not committed)
├── alembic.ini         # Alembic configuration
└── alembic/
    └── versions/       # Migration scripts
```

---

## Data Models

### User

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | Auto-assigned primary key |
| `username` | `str` | Unique username |
| `hashed_pswrd` | `str` | Argon2-hashed password |
| `role` | `str` | `"admin"` or `"user"` (default: `"user"`) |

### Task

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | Auto-assigned primary key |
| `assigner` | `str` | Username of the admin who created the task |
| `assignee` | `str` | Username of the user the task is assigned to |
| `detail` | `str` | Task description |
| `task_status` | `str` | Current status (e.g., `pending`, `in_progress`, `done`) |

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Route | Description | Auth Required |
|---|---|---|---|
| `POST` | `/auth/register` | Register a new user and receive a JWT | No |
| `POST` | `/auth/login` | Login with credentials and receive a JWT | No |

### Users

| Method | Route | Description | Auth Required |
|---|---|---|---|
| `GET` | `/users` | List all users *(5 req/min rate limit)* | No |
| `POST` | `/create_user` | Create a new user | Admin only |

### Tasks

| Method | Route | Description | Auth Required |
|---|---|---|---|
| `GET` | `/tasks` | List all tasks *(Redis cached, 30s TTL)* | No |
| `POST` | `/create_task` | Create a new task | No |
| `PUT` | `/task_update` | Update a task's status by ID | Authenticated user |
| `DELETE` | `/del_task` | Delete a task by ID | Admin only |

### General

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Health check / home page |

---

## Authentication & Authorization

The API uses **JWT Bearer tokens**. Include the token in the `Authorization` header for protected routes:

```
Authorization: Bearer <your_token>
```

**Roles:**
- `user` — Can update task status (`PUT /task_update`)
- `admin` — Can do everything a user can, plus create users (`POST /create_user`) and delete tasks (`DELETE /del_task`)

Tokens are signed using the `secret_key` and `algorithm` defined in `.env`, and expire after `access_token_expire_minutes` (default: 30 minutes).

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
secret_key=your_super_secret_key_here
algorithm=HS256
access_token_expire_minutes=30
database_url=sqlite+aiosqlite:///./todo.db
local_redis_url=redis://localhost:6379
```

| Variable | Description |
|---|---|
| `secret_key` | Secret used to sign JWT tokens |
| `algorithm` | JWT signing algorithm (e.g., `HS256`) |
| `access_token_expire_minutes` | Token lifetime in minutes |
| `database_url` | Async SQLAlchemy database URL |
| `local_redis_url` | Redis connection URL for caching |

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

# 4. Create the .env file and fill in your values
copy .env.example .env       # or create manually
```

### Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Interactive API docs (Swagger UI) are available at `http://127.0.0.1:8000/docs`.

> **Note:** On first startup, if no tables exist in the database, they are created automatically and seeded with the default users and tasks from `initial_data.py`.

---

## Database Migrations

This project uses **Alembic** for managing schema migrations.

```bash
# Generate a new migration after changing a model
alembic revision --autogenerate -m "describe your change"

# Apply pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1
```

Migration scripts are stored in `alembic/versions/`.

---

## Seeded Data

The following users and tasks are inserted automatically on first startup:

### Users

| ID | Username | Password | Role |
|---|---|---|---|
| 1 | `jamil` | `jameel@123` | admin |
| 2 | `roshan` | `roshan@123` | admin |
| 3 | `hsfassih` | `fassih@1730` | user |
| 4 | `nauman` | `nauman@123` | user |
| 5 | `musadiq` | `musadiq@123` | user |

### Tasks

| ID | Assigner | Assignee | Detail | Status |
|---|---|---|---|---|
| 1 | jamil | hsfassih | Complete project documentation | pending |
| 2 | jamil | nauman | Fix bug in authentication module | in_progress |
| 3 | roshan | musadiq | Review pull requests | pending |
