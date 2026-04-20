<#
.SYNOPSIS
    Creates the k3d cluster with local registry and deploys all Kubernetes manifests from k8s/.

.DESCRIPTION
    1. Creates a k3d cluster named todo-cluster (1 server, 2 agents) with local registry
    2. Builds the Docker image locally
    3. Pushes the image to the k3d local registry (k3d-todo-registry:5000)
    4. Applies all manifests in k8s/
    5. Waits for pods to be Ready and prints the running resources

.NOTES
    The application will be accessible at: http://localhost:8080
    The local registry is automatically available at: k3d-todo-registry:5000
    Requires: docker, k3d, kubectl
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ClusterName     = "todo-cluster"
$RegistryCreateName = "todo-registry"
$RegistryHost    = "k3d-todo-registry"
$RegistryPort    = 5000
$BuildImageName  = "hsfassih/todo-app:latest"
$LocalImageName  = "${RegistryHost}:${RegistryPort}/todo-app:latest"
$Namespace       = "todo-app"

# ── Step 1: Create k3d cluster with registry ──────────────────────────────────
Write-Host "`n[1/5] Creating k3d cluster '$ClusterName' with local registry..." -ForegroundColor Cyan
$existing = k3d cluster list -o json 2>$null | ConvertFrom-Json | Where-Object { $_.name -eq $ClusterName }
if ($existing) {
    Write-Host "       Cluster '$ClusterName' already exists — skipping creation." -ForegroundColor Yellow
} else {
    k3d cluster create $ClusterName `
        --servers 1 --agents 2 `
        --registry-create "${RegistryCreateName}:${RegistryPort}" `
        --port "80:80@loadbalancer" `
        --port "443:443@loadbalancer"
    Write-Host "       Cluster created with local registry at ${RegistryHost}:${RegistryPort}" -ForegroundColor Green
}

$registryExists = k3d registry list -o json 2>$null | ConvertFrom-Json | Where-Object { $_.name -in @($RegistryCreateName, $RegistryHost) }
if (-not $registryExists) {
    Write-Error "[ERROR] Local registry not found. Recreate the cluster with this script or create registry '$RegistryCreateName' and attach it to '$ClusterName'."
    exit 1
}

# ── Step 2: Build Docker image ────────────────────────────────────────────────
Write-Host "`n[2/5] Building Docker image '$BuildImageName'..." -ForegroundColor Cyan
docker build -t $BuildImageName .

# ── Step 3: Tag and push to k3d local registry ────────────────────────────────
Write-Host "`n[3/5] Tagging image for local registry: $LocalImageName..." -ForegroundColor Cyan
docker tag $BuildImageName $LocalImageName
Write-Host "`n[3/5] Pushing image to k3d local registry..." -ForegroundColor Cyan
docker push $LocalImageName
Write-Host "       Image successfully pushed to local registry." -ForegroundColor Green

# ── Step 4: Apply all k8s/ manifests ──────────────────────────────────────────
Write-Host "`n[4/5] Applying all manifests in k8s/..." -ForegroundColor Cyan
kubectl apply -f k8s/

# ── Step 5: Wait for pods and print status ────────────────────────────────────
Write-Host "`n[5/5] Waiting for pods to be Ready in namespace '$Namespace' (timeout: 120s)..." -ForegroundColor Cyan
kubectl wait --for=condition=Ready pods --all -n $Namespace --timeout=120s
Write-Host ""
kubectl get all -n $Namespace

Write-Host "`n[OK] Application deployed. Access it at: http://localhost:8080`n" -ForegroundColor Green
