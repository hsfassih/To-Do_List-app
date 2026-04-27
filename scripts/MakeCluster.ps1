<#
.SYNOPSIS
    Creates the k3d cluster with local registry and deploys all Kubernetes manifests from k8s/.

.DESCRIPTION
    1. Creates a k3d cluster named todo-cluster (1 server, 2 agents) with local registry
    2. Builds the Docker image locally
    3. Tags and pushes required images to the k3d local registry (todo-registry:5000)
    4. Applies all manifests in k8s/
    5. Waits for deployments/statefulsets to be Ready and prints running resources

.NOTES
    The application will be accessible at: http://localhost:8080
    The local registry is available at: todo-registry:5000
    Requires: docker, k3d, kubectl
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ClusterName        = "todo-cluster"
$RegistryCreateName = "todo-registry"
$RegistryHost       = "todo-registry"
$RegistryPort       = 5000
$BuildImageName     = "hsfassih/todo-app:latest"
$LocalImageName     = "${RegistryHost}:${RegistryPort}/todo-app:latest"
$PushImageName      = "localhost:${RegistryPort}/todo-app:latest"
$RedisSourceImage   = "redis:alpine"
$RedisLocalImage    = "${RegistryHost}:${RegistryPort}/redis:alpine"
$RedisPushImage     = "localhost:${RegistryPort}/redis:alpine"
$Namespace          = "todo-app"

function Assert-LastExitCode {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Action
    )

    if ($LASTEXITCODE -ne 0) {
        throw "[ERROR] $Action failed (exit code: $LASTEXITCODE)."
    }
}

function Ensure-K3dKubeAccess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ClusterName
    )

    $contextName = "k3d-$ClusterName"

    k3d kubeconfig merge $ClusterName --kubeconfig-merge-default --kubeconfig-switch-context | Out-Null
    Assert-LastExitCode "k3d kubeconfig merge"

    kubectl config use-context $contextName | Out-Null
    Assert-LastExitCode "kubectl config use-context $contextName"

    $currentServer = kubectl config view --raw --minify -o jsonpath="{.clusters[0].cluster.server}"
    Assert-LastExitCode "kubectl config view"

    if ($currentServer -match "^https://([^:/]+):(\d+)$") {
        $hostName = $Matches[1]
        $port = [int]$Matches[2]

        $hostReachable = $false
        $localhostReachable = $false

        try {
            $hostReachable = (Test-NetConnection -ComputerName $hostName -Port $port -WarningAction SilentlyContinue).TcpTestSucceeded
        } catch {
            $hostReachable = $false
        }

        try {
            $localhostReachable = (Test-NetConnection -ComputerName "127.0.0.1" -Port $port -WarningAction SilentlyContinue).TcpTestSucceeded
        } catch {
            $localhostReachable = $false
        }

        if (-not $hostReachable -and $localhostReachable) {
            Write-Host "       kubeconfig endpoint '$currentServer' is unreachable; switching to https://localhost:$port" -ForegroundColor Yellow
            kubectl config set-cluster $contextName --server "https://localhost:$port" | Out-Null
            Assert-LastExitCode "kubectl config set-cluster $contextName"
        }
    }

    kubectl cluster-info | Out-Null
    Assert-LastExitCode "kubectl cluster-info"
}

# --- Step 1: Create k3d cluster with registry ---
Write-Host "`n[1/5] Creating k3d cluster '$ClusterName' with local registry..." -ForegroundColor Cyan
$clusterExists = (k3d cluster list 2>$null | Select-String -SimpleMatch $ClusterName)
if ($clusterExists) {
    Write-Host "       Cluster '$ClusterName' already exists - skipping creation." -ForegroundColor Yellow
} else {
    k3d cluster create $ClusterName `
        --servers 1 --agents 2 `
        --registry-create "${RegistryCreateName}:${RegistryPort}" `
        --port "80:80@loadbalancer" `
        --port "443:443@loadbalancer" `
        --k3s-arg "--disable=traefik@server:0" `
        --k3s-arg "--disable=servicelb@server:0" 
    Assert-LastExitCode "k3d cluster create $ClusterName"
    Write-Host "       Cluster created with local registry at ${RegistryHost}:${RegistryPort}" -ForegroundColor Green
}

Ensure-K3dKubeAccess -ClusterName $ClusterName

$registryExists = (k3d registry list 2>$null | Select-String -Pattern "$RegistryCreateName|$RegistryHost")
if (-not $registryExists) {
    Write-Error "[ERROR] Local registry not found. Recreate the cluster or create registry '$RegistryCreateName' and attach it to '$ClusterName'."
    exit 1
}

# --- Step 2: Build Docker image ---
Write-Host "`n[2/5] Building Docker image '$BuildImageName'..." -ForegroundColor Cyan
docker build -t $BuildImageName .
Assert-LastExitCode "docker build"

# --- Step 3: Tag and push to k3d local registry ---
Write-Host "`n[3/5] Tagging and pushing image to local registry: $LocalImageName..." -ForegroundColor Cyan
docker tag $BuildImageName $PushImageName
Assert-LastExitCode "docker tag"
docker push $PushImageName
Assert-LastExitCode "docker push"

Write-Host "       Pulling and pushing Redis image to local registry: $RedisLocalImage..." -ForegroundColor Cyan
docker pull $RedisSourceImage
Assert-LastExitCode "docker pull $RedisSourceImage"
docker tag $RedisSourceImage $RedisPushImage
Assert-LastExitCode "docker tag redis"
docker push $RedisPushImage
Assert-LastExitCode "docker push redis"

Write-Host "       Application and Redis images successfully pushed to local registry." -ForegroundColor Green

# --- Step 4: Apply all k8s/ manifests ---
Write-Host "`n[4/5] Applying all manifests in k8s/..." -ForegroundColor Cyan
if (Test-Path "k8s/namespace.yaml") {
    kubectl apply -f k8s/namespace.yaml
    Assert-LastExitCode "kubectl apply -f k8s/namespace.yaml"

    kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/$Namespace --timeout=60s
    Assert-LastExitCode "kubectl wait namespace/$Namespace"
}

kubectl apply -f k8s/
Assert-LastExitCode "kubectl apply -f k8s/"

# --- Step 5: Wait for workloads and print status ---
Write-Host "`n[5/5] Waiting for workloads to be Ready in namespace '$Namespace'..." -ForegroundColor Cyan

$deploymentNames = kubectl get deployments -n $Namespace -o name
Assert-LastExitCode "kubectl get deployments"

foreach ($name in ($deploymentNames -split "`r?`n" | Where-Object { $_ })) {
    kubectl rollout status $name -n $Namespace --timeout=300s
    Assert-LastExitCode "kubectl rollout status $name"
}

$statefulSetNames = kubectl get statefulsets -n $Namespace -o name
Assert-LastExitCode "kubectl get statefulsets"

foreach ($name in ($statefulSetNames -split "`r?`n" | Where-Object { $_ })) {
    kubectl rollout status $name -n $Namespace --timeout=300s
    Assert-LastExitCode "kubectl rollout status $name"
}

Write-Host ""
kubectl get all -n $Namespace
Assert-LastExitCode "kubectl get all"

Write-Host "`n[OK] Application deployed. Access it at: http://localhost:8080" -ForegroundColor Green