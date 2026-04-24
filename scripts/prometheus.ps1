<#
.SYNOPSIS
    Installs or upgrades Prometheus (kube-prometheus-stack) on the current K3d cluster.

.DESCRIPTION
    1. Adds / updates the prometheus-community Helm repo
    2. Creates the 'monitoring' namespace (idempotent)
    3. Installs or upgrades the kube-prometheus-stack Helm chart with K3d-tuned values
    4. Waits for all pods in 'monitoring' to be Ready
    5. Port-forwards Prometheus to localhost:9090 and prints verification instructions

    K3d/K3s-specific adjustments applied:
      - kubeControllerManager, kubeScheduler, kubeEtcd, kubeProxy disabled
        (K3s embeds these in a single binary; their metrics ports are unreachable)
      - All remaining targets (kubelet, kube-state-metrics, node-exporter, apiserver,
        coredns, alertmanager, operator) will show as UP on the /targets page.

.NOTES
    Requires: helm, kubectl, k3d cluster running and kubeconfig pointing to it.
    Prometheus UI will be available at: http://localhost:9090
    Keep this terminal open while using Prometheus.
    To also deploy Grafana run: .\scripts\grafana.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Namespace   = "monitoring"
$ReleaseName = "kube-prometheus-stack"
$RepoName    = "prometheus-community"
$RepoUrl     = "https://prometheus-community.github.io/helm-charts"
$ChartName   = "prometheus-community/kube-prometheus-stack"
$PrometheusPort = 9090

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

# --- Step 3: Build inline values (K3d/K3s tuned) ---
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
  enabled: false
"@

$TempValuesFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.yaml'
$ValuesYaml | Set-Content -Path $TempValuesFile -Encoding UTF8

# --- Step 4: Install or upgrade the chart ---
Write-Host "`n[3/5] Installing / upgrading '$ReleaseName' in namespace '$Namespace'..." -ForegroundColor Cyan
$releaseExists = (helm list -n $Namespace 2>$null | Select-String -Pattern "^$ReleaseName\s")
if ($releaseExists) {
    Write-Host "       Release exists - upgrading..." -ForegroundColor Yellow
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

# --- Step 5: Wait for all pods to be Ready ---
Write-Host "`n[4/5] Waiting for all pods in '$Namespace' to be Ready (timeout: 3m)..." -ForegroundColor Cyan
kubectl wait --for=condition=Ready pods --all -n $Namespace --timeout=180s
Write-Host ""
kubectl get pods -n $Namespace

# --- Step 6: Port-forward Prometheus ---
Write-Host "`n[5/5] Starting port-forward: localhost:$PrometheusPort -> Prometheus..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Prometheus UI : http://localhost:$PrometheusPort" -ForegroundColor Green
Write-Host "  Targets page  : http://localhost:$PrometheusPort/targets" -ForegroundColor Green
Write-Host ""
Write-Host "  All the following target groups should show as UP:" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-alertmanager" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-kube-state-metrics" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-node-exporter (one entry per node)" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-operator" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-prometheus (self-scrape)" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-apiserver" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-kubelet / cadvisor" -ForegroundColor Yellow
Write-Host "    - kube-prometheus-stack-coredns" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop the port-forward." -ForegroundColor DarkGray
Write-Host ""

kubectl port-forward svc/${ReleaseName}-prometheus $PrometheusPort`:$PrometheusPort -n $Namespace
