# To-Do List API

A production-ready RESTful To-Do List API built with **FastAPI**, featuring JWT authentication, role-based access control, async SQLite persistence, Redis caching, and rate limiting.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
  - [Docker](#docker)
  - [docker-compose](#docker-compose)
  - [k3d (Kubernetes with Local Cluster)](#k3d-kubernetes-with-local-cluster)
  - [kubectl (Kubernetes CLI)](#kubectl-kubernetes-cli)
  - [Helm (Package Manager for Kubernetes)](#helm-package-manager-for-kubernetes)

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

### k3d (Kubernetes with Local Cluster)

k3d allows you to run Kubernetes locally using Docker. Use these commands to create and manage a k3d cluster for this application.

#### Prerequisites

- Docker installed and running
- `k3d` installed ([Installation Guide](https://k3d.io/#installation))
- `kubectl` installed ([Installation Guide](https://kubernetes.io/docs/tasks/tools/))

#### 1. Create a k3d cluster with 1 server and 2 agents

```bash
k3d cluster create todo-cluster --servers 1 --agents 2 -p "8080:80@loadbalancer"
```

*Purpose: Creates a local Kubernetes cluster named `todo-cluster` with 1 server node and 2 agent nodes. Port mapping `8080:80@loadbalancer` routes host port 8080 to the cluster's loadbalancer port 80.*

#### 2. Verify the cluster is running

```bash
kubectl cluster-info
```

*Purpose: Displays information about the Kubernetes control plane and cluster.*

#### 3. Build the Docker image

```bash
docker build -t hsfassih/todo-app .
```

*Purpose: Builds the Docker image from the Dockerfile in the current directory.*

#### 4. Import the image into k3d

```bash
k3d image import hsfassih/todo-app -c todo-cluster
```

*Purpose: Makes the Docker image available inside the k3d cluster without pushing to Docker Hub.*

#### 5. Deploy all Kubernetes manifests

```bash
kubectl apply -f k8s/
```

*Purpose: Applies all YAML files in the `k8s/` folder (namespace, secret, redis, app, and ingress).*

#### 6. Verify all resources are running

```bash
kubectl get all -n todo-app
```

*Purpose: Lists all pods, services, and deployments in the `todo-app` namespace. All pods should be in `Running` state.*

#### 7. Access the application

Open your browser and navigate to:

```
http://localhost:8080
```

*Purpose: Accesses the deployed application. k3d routes traffic from `localhost:8080` through the loadbalancer to the Traefik Ingress controller and then to your app.*

#### 8. Delete the cluster

```bash
k3d cluster delete todo-cluster
```

*Purpose: Removes the k3d cluster and all associated resources.*

#### 9. List all k3d clusters

```bash
k3d cluster list
```

*Purpose: Shows all k3d clusters running on your machine.*

#### 10. Stop a cluster without deleting it

```bash
k3d cluster stop todo-cluster
```

*Purpose: Stops the cluster while preserving all data and configuration for later restart.*

#### 11. Start a stopped cluster

```bash
k3d cluster start todo-cluster
```

*Purpose: Restarts a previously stopped cluster.*

### kubectl (Kubernetes CLI)

kubectl is the command-line tool for interacting with Kubernetes clusters. Use these commands to manage and monitor your deployed application.

#### 1. View all pods in the namespace

```bash
kubectl get pods -n todo-app
```

*Purpose: Lists all pods in the `todo-app` namespace with their status.*

#### 2. View all services

```bash
kubectl get svc -n todo-app
```

*Purpose: Lists all services (ClusterIP, LoadBalancer, etc.) with their internal IPs and ports.*

#### 3. View all deployments

```bash
kubectl get deployments -n todo-app
```

*Purpose: Lists all deployments with their replica count and readiness status.*

#### 4. View the Ingress configuration

```bash
kubectl get ingress -n todo-app
```

*Purpose: Shows the Ingress rules that route external traffic to your services.*

#### 5. Stream live logs from the app deployment

```bash
kubectl logs -n todo-app -f deployment/todo-app
```

*Purpose: Displays real-time logs from the app pod. Press `Ctrl+C` to exit.*

#### 6. Stream logs from Redis

```bash
kubectl logs -n todo-app -f deployment/redis
```

*Purpose: Displays real-time logs from the Redis pod.*

#### 7. View logs from a specific pod

```bash
kubectl logs -n todo-app <pod-name>
```

*Purpose: Shows logs from a specific pod. Use `kubectl get pods -n todo-app` to find pod names.*

#### 8. View the last N lines of logs

```bash
kubectl logs -n todo-app deployment/todo-app --tail=50
```

*Purpose: Shows only the last 50 lines of logs.*

#### 9. View logs from the last X time period

```bash
kubectl logs -n todo-app deployment/todo-app --since=5m
```

*Purpose: Shows logs from the last 5 minutes (`5m`, `1h`, `30s`, etc.).*

#### 10. Describe a pod (detailed information for troubleshooting)

```bash
kubectl describe pod <pod-name> -n todo-app
```

*Purpose: Displays detailed information about a pod, including events, status, and resource allocation. Useful for debugging pod failures.*

#### 11. Describe a deployment

```bash
kubectl describe deployment todo-app -n todo-app
```

*Purpose: Shows detailed information about the deployment, including replicas, selectors, and pod template specifications.*

#### 12. Get all resources in the namespace

```bash
kubectl get all -n todo-app
```

*Purpose: Lists all resources (pods, services, deployments, statefulsets, etc.) in one view.*

#### 13. Execute a command inside a pod

```bash
kubectl exec -it -n todo-app deployment/todo-app -- /bin/sh
```

*Purpose: Opens an interactive shell inside the app pod for debugging.*

#### 14. Run a single command inside a pod

```bash
kubectl exec -n todo-app <pod-name> -- redis-cli -h redis-service ping
```

*Purpose: Runs a specific command inside a pod without opening a shell.*

#### 15. Scale the deployment (not recommended for this app due to SQLite)

```bash
kubectl scale deployment todo-app --replicas=3 -n todo-app
```

*Purpose: Changes the number of running pod replicas. For this app, keep replicas at 1 because SQLite does not support concurrent multi-pod writes.*

#### 16. Roll back to a previous deployment

```bash
kubectl rollout undo deployment/todo-app -n todo-app
```

*Purpose: Reverts to the previous deployment state if the current one has issues.*

#### 17. Check deployment rollout history

```bash
kubectl rollout history deployment/todo-app -n todo-app
```

*Purpose: Shows the revision history of the deployment.*

#### 18. View all events in the namespace

```bash
kubectl get events -n todo-app
```

*Purpose: Lists all events (pod creations, failures, warnings, etc.) useful for troubleshooting.*

#### 19. Delete a pod (automatically restarts due to deployment)

```bash
kubectl delete pod <pod-name> -n todo-app
```

*Purpose: Removes a pod, which triggers the deployment to automatically create a new one.*

#### 20. Delete all resources in the namespace

```bash
kubectl delete all --all -n todo-app
```

*Purpose: Removes all pods, services, and deployments but keeps the namespace. Use with caution.*

#### 21. Delete the entire namespace (and all its resources)

```bash
kubectl delete namespace todo-app
```

*Purpose: Permanently removes the namespace and everything in it.*

#### Quick Reference Commands

```bash
# Check cluster status
kubectl cluster-info

# Get pods with detailed info (including node assignment)
kubectl get pods -n todo-app -o wide

# Get resource usage (CPU, memory) — requires metrics-server
kubectl top pods -n todo-app

# Watch pod status in real-time
kubectl get pods -n todo-app -w

# Forward a local port to a pod
kubectl port-forward -n todo-app svc/todo-app-service 8081:80

# Apply only specific file
kubectl apply -f k8s/app.yaml

# Dry-run (see what would be applied without actually applying)
kubectl apply -f k8s/ --dry-run=client
```

### Helm (Package Manager for Kubernetes)

Helm is a package manager for Kubernetes that simplifies deploying and managing applications. Use these commands to manage your Helm charts.

#### Prerequisites

- Helm installed ([Installation Guide](https://helm.sh/docs/intro/install/))
- kubectl configured and connected to your Kubernetes cluster
- The `todo-app-chart` Helm chart in your project directory

#### 1. Verify Helm is installed

```bash
helm version
```

*Purpose: Displays the installed Helm version and verifies connectivity to the Kubernetes cluster.*

#### 2. Lint the Helm chart (check for errors)

```bash
helm lint ./todo-app-chart
```

*Purpose: Validates the chart for syntax errors, missing fields, and best practices. Run before installing to catch issues early.*

#### 3. Preview what the chart will render (dry-run)

```bash
helm template todo-app ./todo-app-chart --debug
```

*Purpose: Renders all templates and displays the final Kubernetes manifests without actually deploying them. Useful for debugging template issues.*

#### 4. Install the Helm chart

```bash
helm install todo-app ./todo-app-chart -n todo-app --create-namespace
```

*Purpose: Installs the chart as a release named `todo-app` in the `todo-app` namespace. The `--create-namespace` flag creates the namespace if it doesn't exist.*

#### 5. Install with custom values (override defaults)

```bash
helm install todo-app ./todo-app-chart -n todo-app --create-namespace \
  --set replicaCount=5 \
  --set image.tag=v1.0
```

*Purpose: Overrides specific values from `values.yaml`. Common overrides: `replicaCount` (number of pods), `image.tag` (Docker image version), `image.repository` (image URL).*

#### 6. Verify the release was installed

```bash
helm list -n todo-app
```

*Purpose: Lists all Helm releases in the `todo-app` namespace with their status and revision number.*

#### 7. View the status of a release

```bash
helm status todo-app -n todo-app
```

*Purpose: Shows detailed information about the deployed release, including resource names and deployment status.*

#### 8. Get the values currently in use by a release

```bash
helm get values todo-app -n todo-app
```

*Purpose: Displays the actual values being used by the deployed release (merged from defaults and `--set` overrides).*

#### 9. View all Kubernetes manifests for a release

```bash
helm get manifest todo-app -n todo-app
```

*Purpose: Shows all rendered Kubernetes YAML files for the deployed release.*

#### 10. Upgrade a release (e.g., change replica count)

```bash
helm upgrade todo-app ./todo-app-chart -n todo-app --set replicaCount=7
```

*Purpose: Modifies an existing release without reinstalling. Useful for scaling, updating image tags, or changing configuration.*

#### 11. Upgrade and reinstall if release doesn't exist

```bash
helm upgrade --install todo-app ./todo-app-chart -n todo-app --create-namespace
```

*Purpose: Installs the chart if it doesn't exist, or upgrades it if it does. Idempotent operation.*

#### 12. View the release history

```bash
helm history todo-app -n todo-app
```

*Purpose: Shows all revisions of the release with timestamps, status, and descriptions. Useful for tracking changes.*

#### 13. Roll back to a previous revision

```bash
helm rollback todo-app 1 -n todo-app
```

*Purpose: Reverts the release to a previous revision. Example: `helm rollback todo-app 1` rolls back to revision 1. Use `helm history` to see available revisions.*

#### 14. Uninstall (delete) a release

```bash
helm uninstall todo-app -n todo-app
```

*Purpose: Removes the release from Kubernetes. By default, this keeps persistent volumes (data) intact. Use `--no-hooks` to skip pre-delete hooks.*

#### 15. Uninstall and delete all resources including persistent volumes

```bash
helm uninstall todo-app -n todo-app --no-hooks
```

*Purpose: Deletes the release and removes all associated Kubernetes objects (pods, services, etc.).*

#### 16. Search for available Helm charts (from repositories)

```bash
helm search repo redis
```

*Purpose: Searches installed Helm repositories for charts matching the query. Requires adding repos first.*

#### 17. Add a Helm repository

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```

*Purpose: Adds a remote Helm repository so you can install charts from it. Popular repos: Bitnami, Stable, etc.*

#### 18. Update Helm repository cache

```bash
helm repo update
```

*Purpose: Fetches the latest chart metadata from all added repositories.*

#### 19. List all added Helm repositories

```bash
helm repo list
```

*Purpose: Shows all configured Helm repositories and their URLs.*

#### 20. Test Helm chart templates with a values file

```bash
helm template todo-app ./todo-app-chart -f custom-values.yaml
```

*Purpose: Renders templates using a custom values file instead of the default `values.yaml`. Useful for testing different configurations.*

#### Quick Reference Commands

```bash
# Full deployment workflow
helm lint ./todo-app-chart
helm template todo-app ./todo-app-chart --debug
helm install todo-app ./todo-app-chart -n todo-app --create-namespace
helm status todo-app -n todo-app
helm list -n todo-app

# Upgrade and rollback workflow
helm upgrade todo-app ./todo-app-chart -n todo-app --set replicaCount=5
helm history todo-app -n todo-app
helm rollback todo-app 1 -n todo-app

# Cleanup
helm uninstall todo-app -n todo-app
```

---

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


