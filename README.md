# To-Do List API

A production-ready RESTful To-Do List API built with **FastAPI**, featuring JWT authentication, role-based access control, async SQLite persistence, Redis caching, and rate limiting.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
  - [Docker](#docker)
  - [docker-compose](#docker-compose)

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

### Docker

To containerize and deploy the application using Docker:

1. **Login to Docker Hub** (if not already logged in):
   ```bash
   docker login
   ```
   *Purpose: Authenticates your Docker CLI with Docker Hub to enable pushing and pulling images.*

2. **Build the Docker image**:
   ```bash
   docker build -t hsfassih/todo-app .
   ```
   *Purpose: Creates a Docker image from the Dockerfile in the current directory, tagging it as `hsfassih/todo-app`.*

3. **Push the image to Docker Hub**:
   ```bash
   docker push hsfassih/todo-app
   ```
   *Purpose: Uploads the built image to your Docker Hub repository, making it available for deployment on any machine.*

4. **Pull the image from Docker Hub** (on the target machine or to test locally):
   ```bash
   docker pull hsfassih/todo-app
   ```
   *Purpose: Downloads the image from Docker Hub to the local machine, ensuring you have the latest version.*

5. **Run the application**:
   ```bash
   docker run -p 8080:8080 hsfassih/todo-app
   ```
   *Purpose: Starts a container from the image, mapping port 8080 on the host to port 8080 in the container, allowing access to the API at `http://localhost:8080`.*

### docker-compose

Use docker-compose to orchestrate both the app and Redis services together with proper environment variable management.


**Important**: Never commit `.env` — it's already in `.gitignore`. In production, pass secrets via CI/CD or orchestration platforms (Kubernetes, Docker Swarm, etc.).

#### 2. Build and start all services

```bash
# First time: build the image and start both app and Redis containers
docker-compose up --build

# Subsequent times: just start without rebuilding
docker-compose up
```

*Purpose: The `--build` flag rebuilds the Docker image from the Dockerfile. The app will automatically wait for Redis to be healthy before starting.*

#### 3. Run services in the background (detached mode)

```bash
docker-compose up -d --build
```

*Purpose: Starts services in the background. Use this for long-running deployments where you don't need to see logs in your terminal.*

#### 4. View logs from all services

```bash
# View logs from all services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs from only the app service
docker-compose logs -f app

# View logs from only the Redis service
docker-compose logs -f redis
```

#### 5. Stop all services

```bash
docker-compose stop
```

*Purpose: Gracefully stops containers but preserves volumes (your SQLite data remains).*

#### 6. Stop and remove all services

```bash
docker-compose down
```

*Purpose: Stops and removes containers. Volumes persist by default (use `-v` to delete volumes too).*

#### 7. Restart services

```bash
docker-compose restart
```

*Purpose: Restarts all containers without stopping them entirely.*

#### 8. Execute commands inside a running container

```bash
# Open a shell inside the app container
docker-compose exec app sh

# Run a one-off command (e.g., check migrations)
docker-compose exec app alembic current
```

#### 9. Rebuild services after code changes

```bash
docker-compose up --build
```

*Purpose: Rebuilds the Docker image from your updated source code and restarts containers.*

#### 10. Clean up everything (containers, volumes, networks)

```bash
docker-compose down -v
```

*Purpose: Removes all resources created by docker-compose, including the SQLite database volume. Use carefully!*

#### Verify the API is running

Once services are up, test the API:

```bash
# Health check
curl http://localhost:8080/docs

# Or in PowerShell (Windows)
Invoke-WebRequest http://localhost:8080/docs
```

The Swagger UI should load at `http://localhost:8080/docs`.

#### Troubleshooting

| Issue | Solution |
|---|---|
| Port 8080 already in use | Change port in `docker-compose.yaml`: `ports: ["9000:8080"]` |
| Redis connection fails | Verify `REDIS_URL=redis://redis:6379` in `.env` (use service name, not `localhost`) |
| App crashes on startup | Run `docker-compose logs -f app` to see detailed error messages |
| Database not persisting | Check that `volumes: - sqlite_data:/app` is in `docker-compose.yaml` |
| `pydantic_settings` not found | Rebuild image: `docker-compose up --build` |

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

