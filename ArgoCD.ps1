<#
.SYNOPSIS
    Sets up and runs ArgoCD on the current k3d cluster.

.DESCRIPTION
    1. Creates the argocd namespace
    2. Installs all ArgoCD components
    3. Waits for all pods to be Ready
    4. Patches the server to run in HTTP (insecure) mode
    5. Restarts + waits for the argocd-server rollout
    6. Applies the ArgoCD Application manifest (argocd-app.yaml)
    7. Starts a port-forward to expose the ArgoCD UI on localhost:8080
    8. Prints the initial admin password

.NOTES
    Keep this terminal open while using the ArgoCD UI.
    ArgoCD UI will be available at: http://localhost:8080
    Default credentials: admin / <printed password>
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Step 1: Create namespace ──────────────────────────────────────────────────
Write-Host "`n[1/7] Creating argocd namespace..." -ForegroundColor Cyan
kubectl create namespace argocd # --dry-run=client -o yaml | kubectl apply -f -

# ── Step 2: Install ArgoCD ────────────────────────────────────────────────────
Write-Host "`n[2/7] Installing ArgoCD components..." -ForegroundColor Cyan
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# ── Step 3: Wait for all pods to be Ready ─────────────────────────────────────
Write-Host "`n[3/7] Waiting for all ArgoCD pods to be Ready (timeout: 300s)..." -ForegroundColor Cyan
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s
kubectl get pods -n argocd

# ── Step 4: Patch server to HTTP mode ─────────────────────────────────────────
Write-Host "`n[4/7] Enabling HTTP (insecure) mode on argocd-server..." -ForegroundColor Cyan
kubectl patch configmap argocd-cmd-params-cm -n argocd --type merge --patch-file argocd-patch.yaml

# ── Step 5: Restart and wait for argocd-server ───────────────────────────────
Write-Host "`n[5/7] Restarting argocd-server deployment..." -ForegroundColor Cyan
kubectl rollout restart deployment argocd-server -n argocd
kubectl rollout status deployment argocd-server -n argocd

# ── Step 6: Apply ArgoCD Application manifest ─────────────────────────────────
Write-Host "`n[6/7] Applying ArgoCD Application manifest (argocd-app.yaml)..." -ForegroundColor Cyan
kubectl apply -f argocd-app.yaml

# ── Step 7: Print initial admin password ──────────────────────────────────────
Write-Host "`n[7/7] Retrieving initial admin password..." -ForegroundColor Cyan
$encodedPassword = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
$password = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encodedPassword))
Write-Host "`n  ArgoCD UI   : http://localhost:8080" -ForegroundColor Green
Write-Host "  Username    : admin" -ForegroundColor Green
Write-Host "  Password    : $password" -ForegroundColor Green

# ── Port-forward (blocking — keeps UI accessible) ─────────────────────────────
Write-Host "`n[INFO] Starting port-forward on localhost:8080 -> argocd-server:80" -ForegroundColor Yellow
Write-Host "       Press Ctrl+C to stop.`n" -ForegroundColor Yellow
kubectl port-forward svc/argocd-server -n argocd 8080:80
