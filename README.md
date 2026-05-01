# To-Do List App

Production-oriented FastAPI backend with JWT authentication, role-based authorization, Redis caching, and a full DevSecOps delivery stack (Docker, Kubernetes, Helm, ArgoCD, Terraform, and GitHub Actions).

## Highlights

- FastAPI REST API under `/api/v1`
- JWT auth (`/auth/register`, `/auth/login`) with admin/user RBAC
- Async persistence with SQLModel + SQLAlchemy + SQLite (`aiosqlite`)
- Redis response caching (`/tasks`) and request rate limiting (`/users`)
- Local container workflow with Docker Compose
- Kubernetes manifests in `k8s/` for direct apply
- Helm chart in `todo-app-chart/` with `local`, `dev`, and `prod` value overlays
- ArgoCD App of Apps setup in `argocd/`
- Lambda packaging and Terraform deployment workflow

## Repository Structure

```text
.
|-- src/                    # FastAPI source code
|-- alembic/                # Database migrations
|-- k8s/                    # Raw Kubernetes manifests
|-- todo-app-chart/         # Helm chart and values files
|-- argocd/                 # Child ArgoCD application manifests
|-- scripts/                # PowerShell automation scripts
|-- terraform/              # Terraform root module + submodules
|-- lambda/                 # Lambda handlers and requirements
|-- memory-bank/            # Project memory/context files
|-- docker-compose.yaml
|-- dockerfile
`-- .github/workflows/      # CI and Lambda deploy workflows
```

## Prerequisites

- Python 3.14 (or compatible 3.x runtime)
- Docker
- Optional for Kubernetes path: `kubectl`, `k3d`, `helm`
- Optional for IaC path: Terraform

## Environment Variables

Create `.env` in the repository root:

```env
secret_key=replace-with-a-strong-random-value
algorithm=HS256
access_token_expire_minutes=30
database_url=sqlite+aiosqlite:///./data/todo_list.db
redis_url=redis://localhost:6379
```

Notes:
- `src/auth/database.py` currently builds the SQLite URL internally and does not consume `database_url` from settings.
- `src/config.py` reads `.env` using `env_file = "../.env"`, so launching from `src/` is the most reliable local flow.

## Run Locally (without Docker)

From repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r src/requirements.txt
docker run -d --name redis-local -p 6379:6379 redis:alpine
cd src
uvicorn main:app --reload --port 8080
```

Swagger UI: `http://localhost:8080/docs`

## Run with Docker Compose

From repository root:

```powershell
docker compose up --build
```

The app is exposed on `http://localhost:8080`.

## Kubernetes Quick Start (k3d)

This repository includes scripted local cluster automation.

1. Create cluster, build image, push to local registry, apply manifests:

```powershell
.\scripts\MakeCluster.ps1
```

2. Deploy/upgrade Helm release (base values):

```powershell
.\scripts\SetHelm.ps1
```

3. Deploy with local overrides:

```powershell
.\scripts\SetHelm.ps1 --deploy values-local.yaml
```

4. Verify:

```powershell
kubectl get all -n todo-app
```

Local registry image source used by manifests/values: `todo-registry:5000`.

## Helm and ArgoCD Notes

- `scripts/SetHelm.ps1` performs lint + upgrade/install (`--take-ownership`) and uses Helm v4 server-side apply flags.
- If `PrometheusRule` CRD is missing, the script auto-disables `monitoring.prometheusRule.enabled`.
- ArgoCD root app: `argocd-root-app.yaml`
- Child apps:
  - `argocd/apps/todo-app-dev.yaml`
  - `argocd/apps/todo-app-prod.yaml`

Bootstrap ArgoCD on cluster:

```powershell
.\scripts\ArgoCD.ps1
```

## Monitoring Helpers

- Prometheus stack script: `scripts/prometheus.ps1`
- Grafana enablement script: `scripts/grafana.ps1`

## API Surface Summary

Base prefix: `/api/v1`

Auth:
- `POST /auth/register`
- `POST /auth/login`

Users:
- `GET /users` (rate limited)
- `POST /users/create` (admin)
- `PUT /users/update{username}` (admin)
- `DELETE /users/delete{username}` (admin)

Tasks:
- `GET /tasks` (cached)
- `POST /tasks/create`
- `PUT /tasks/update{id}` (authenticated)
- `DELETE /tasks/delete{id}` (admin)

Note: update/delete route path parameter formatting is currently `update{id}` and `delete{id}` (without `/`).

## Database and Migrations

Alembic is configured in `alembic/` and `alembic.ini`.

```powershell
alembic revision --autogenerate -m "describe-change"
alembic upgrade head
alembic downgrade -1
```

## Lambda and Terraform

- Lambda handlers are in `lambda/`.
- Terraform root module is in `terraform/`.
- CI workflow: `.github/workflows/ci.yml`
- Lambda deploy workflow: `.github/workflows/deploy-lambda.yml`

The Lambda workflow packages functions, uploads ZIP artifacts to S3, then runs Terraform apply.

## Known Gaps

- No automated test suite is currently present.
- Seed task statuses include `in_progress` while task validation expects `in progress`.
- Some config loading is split between `pydantic-settings` and direct `dotenv/os.getenv` usage.
