<#
.SYNOPSIS
    Installs or upgrades Grafana (via kube-prometheus-stack) on the current K3d cluster.

.DESCRIPTION
    1. Adds / updates the prometheus-community Helm repo
    2. Creates the 'monitoring' namespace (idempotent)
    3. Installs or upgrades the kube-prometheus-stack Helm chart with Grafana enabled
       and all other components disabled (Prometheus, Alertmanager, exporters).
       Use this script alongside prometheus.ps1 if you want both stacks running,
       OR run prometheus.ps1 alone (it installs the full stack with Grafana disabled).
    4. Waits for the Grafana pod to be Ready
    5. Port-forwards Grafana to localhost:3000 and prints login instructions

    If you already have kube-prometheus-stack installed via prometheus.ps1, this script
    upgrades the same release to enable Grafana on top of the existing Prometheus stack.

.NOTES
    Requires: helm, kubectl, k3d cluster running and kubeconfig pointing to it.
    Grafana UI will be available at: http://localhost:3000
    Default credentials: admin / admin
    Keep this terminal open while using Grafana.
    To deploy Prometheus first run: .\scripts\prometheus.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Namespace   = "monitoring"
$ReleaseName = "kube-prometheus-stack"
$RepoName    = "prometheus-community"
$RepoUrl     = "https://prometheus-community.github.io/helm-charts"
$ChartName   = "prometheus-community/kube-prometheus-stack"
$GrafanaPort = 3000

# --- Step 1: Add / update Helm repo ---
Write-Host "`n[1/5] Adding Helm repo '$RepoName'..." -ForegroundColor Cyan
$repoExists = (helm repo list 2>$null | Select-String -Pattern "^$RepoName\s")
if ($repoExists) {
    Write-Host "       Repo '$RepoName' already registered - updating..." -ForegroundColor Yellow
} else {
    helm repo add $RepoName $RepoUrl
}
helm repo update
Write-Host "       Repo ready." -ForegroundColor Green

# --- Step 2: Create namespace (idempotent) ---
Write-Host "`n[2/5] Ensuring namespace '$Namespace' exists..." -ForegroundColor Cyan
kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -

# --- Step 3: Build inline values ---
# If prometheus.ps1 was already run, this upgrade re-enables Grafana within the
# same release so both Prometheus and Grafana share one chart installation.
$ValuesYaml = @"
kubeControllerManager:
  enabled: false
kubeScheduler:
  enabled: false
kubeEtcd:
  enabled: false
kubeProxy:
  enabled: false

prometheus:
  prometheusSpec:
    retention: 24h
    resources:
      requests:
        cpu: "200m"
        memory: "512Mi"
      limits:
        cpu: "500m"
        memory: "1Gi"

alertmanager:
  alertmanagerSpec:
    resources:
      requests:
        cpu: "50m"
        memory: "64Mi"
      limits:
        cpu: "100m"
        memory: "128Mi"

nodeExporter:
  enabled: true

kubeStateMetrics:
  enabled: true

grafana:
  enabled: true
  adminPassword: "admin"
  service:
    type: ClusterIP
  persistence:
    enabled: false
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "200m"
      memory: "256Mi"
  defaultDashboardsEnabled: true
  defaultDashboardsTimezone: utc
"@

$TempValuesFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.yaml'
$ValuesYaml | Set-Content -Path $TempValuesFile -Encoding UTF8

# --- Step 4: Install or upgrade the chart ---
Write-Host "`n[3/5] Installing / upgrading '$ReleaseName' with Grafana enabled in '$Namespace'..." -ForegroundColor Cyan
$releaseExists = (helm list -n $Namespace 2>$null | Select-String -Pattern "^$ReleaseName\s")
if ($releaseExists) {
    Write-Host "       Release exists - upgrading to enable Grafana..." -ForegroundColor Yellow
    helm upgrade $ReleaseName $ChartName `
        --namespace $Namespace `
        --values $TempValuesFile `
        --wait `
        --timeout 5m
} else {
    helm install $ReleaseName $ChartName `
        --namespace $Namespace `
        --values $TempValuesFile `
        --wait `
        --timeout 5m
}
Remove-Item $TempValuesFile -Force
Write-Host "       Chart deployed." -ForegroundColor Green

# --- Step 5: Wait for Grafana pod specifically ---
Write-Host "`n[4/5] Waiting for Grafana pod to be Ready (timeout: 3m)..." -ForegroundColor Cyan
kubectl wait --for=condition=Ready pods `
    --selector="app.kubernetes.io/name=grafana" `
    -n $Namespace `
    --timeout=180s
Write-Host ""
kubectl get pods -n $Namespace

# --- Step 6: Port-forward Grafana ---
Write-Host "`n[5/5] Starting port-forward: localhost:$GrafanaPort -> Grafana..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Grafana UI  : http://localhost:$GrafanaPort" -ForegroundColor Green
Write-Host "  Username    : admin" -ForegroundColor Green
Write-Host "  Password    : admin" -ForegroundColor Green
Write-Host ""
Write-Host "  Default Kubernetes dashboards to verify:" -ForegroundColor Yellow
Write-Host "    Dashboards -> Browse -> Kubernetes / Nodes" -ForegroundColor Yellow
Write-Host "      Shows: node CPU, memory, disk I/O (from node-exporter data)" -ForegroundColor Yellow
Write-Host "    Dashboards -> Browse -> Kubernetes / Compute Resources / Pod" -ForegroundColor Yellow
Write-Host "      Shows: per-pod CPU and memory (from kube-state-metrics data)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop the port-forward." -ForegroundColor DarkGray
Write-Host ""

kubectl port-forward svc/${ReleaseName}-grafana $GrafanaPort`:80 -n $Namespace
