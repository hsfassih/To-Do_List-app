<#
.SYNOPSIS
    Sets up and runs ArgoCD with the App of Apps pattern.

.DESCRIPTION
    1. Creates the argocd namespace
    2. Installs all ArgoCD components
    3. Waits for all pods to be Ready
    4. Patches the server to run in HTTP (insecure) mode
    5. Restarts + waits for the argocd-server rollout
    6. Kills any existing process on port 8080
    7. Removes the legacy single-app (if it exists)
    8. Applies the ROOT ArgoCD Application (App of Apps pattern)
    9. Waits for child apps to sync and appear
    10. Prints the initial admin password and starts port-forward

.NOTES
    Keep this terminal open while using the ArgoCD UI.
    ArgoCD UI will be available at: http://localhost:8080
    Default credentials: admin / <printed password>

    The App of Apps pattern means:
    - root-app (the one file you apply) watches argocd/apps/ for child Application YAMLs
    - Child apps (todo-app-prod, todo-app-dev) each deploy their own Helm release
    - Deleting a child app YAML from Git automatically removes it from the cluster
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Step 1: Create namespace ---
Write-Host "`n[1/10] Creating argocd namespace..." -ForegroundColor Cyan
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# --- Step 2: Install ArgoCD ---
Write-Host "`n[2/10] Installing ArgoCD components..." -ForegroundColor Cyan
# Server-side apply avoids large client-side last-applied annotations on CRDs.
kubectl apply --server-side --force-conflicts -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# --- Step 3: Wait for all pods to be Ready ---
Write-Host "`n[3/10] Waiting for all ArgoCD pods to be Ready (timeout: 180s)..." -ForegroundColor Cyan
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=180s
kubectl get pods -n argocd

# --- Step 4: Patch server to HTTP mode ---
Write-Host "`n[4/10] Enabling HTTP (insecure) mode on argocd-server..." -ForegroundColor Cyan
kubectl patch configmap argocd-cmd-params-cm -n argocd --type merge --patch-file argocd-patch.yaml

# --- Step 5: Restart and wait for argocd-server ---
Write-Host "`n[5/10] Restarting argocd-server deployment..." -ForegroundColor Cyan
kubectl rollout restart deployment argocd-server -n argocd
kubectl rollout status deployment argocd-server -n argocd

# --- Step 6: Kill any existing process on port 8080 ---
Write-Host "`n[6/10] Cleaning up any existing port-forward on port 8080..." -ForegroundColor Cyan
try {
    $portProcess = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq "Listen" } |
        Select-Object -First 1
    if ($portProcess) {
        $processId = $portProcess.OwningProcess
        Write-Host "  Found process on port 8080 (PID: $processId), stopping it..." -ForegroundColor Yellow
        Stop-Process -Id $processId -Force
        Start-Sleep -Seconds 1
        Write-Host "  Port 8080 is now free." -ForegroundColor Green
    } else {
        Write-Host "  Port 8080 is already free." -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not check port 8080 (OK if netstat unavailable)." -ForegroundColor Gray
}

# --- Step 7: Remove legacy single-app (if it exists) ---
Write-Host "`n[7/10] Cleaning up legacy single-app (todo-app)..." -ForegroundColor Cyan
$legacyAppExists = kubectl get application todo-app -n argocd --ignore-not-found -o name
if ($legacyAppExists) {
    Write-Host "  Found legacy app 'todo-app', deleting it..." -ForegroundColor Yellow
    kubectl delete application todo-app -n argocd --ignore-not-found
    Start-Sleep -Seconds 2
    Write-Host "  Legacy app removed." -ForegroundColor Green
} else {
    Write-Host "  No legacy app found (first run or already removed)." -ForegroundColor Green
}

# --- Step 8: Apply ROOT ArgoCD Application (App of Apps pattern) ---
Write-Host "`n[8/10] Applying ROOT ArgoCD Application (App of Apps pattern)..." -ForegroundColor Cyan
Write-Host "       This will create todo-app-prod and todo-app-dev as child apps." -ForegroundColor Gray
kubectl apply -f argocd-root-app.yaml

# --- Step 9: Wait for child apps to appear ---
Write-Host "`n[9/10] Waiting for root-app to create child Applications..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
$maxRetries = 3
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $appCount = (kubectl get application -n argocd --no-headers 2>$null | Measure-Object -Line).Lines
        if ($appCount -ge 3) {
            Write-Host "  [OK] All 3 applications detected (root-app, todo-app-prod, todo-app-dev)" -ForegroundColor Green
            kubectl get applications -n argocd
            break
        } else {
            Write-Host "  Found $appCount app(s), waiting for 3..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    } catch {
        Start-Sleep -Seconds 5
    }
    $retryCount++
}

# --- Step 10: Print admin password and start port-forward ---
Write-Host "`n[10/10] Retrieving initial admin password..." -ForegroundColor Cyan
try {
    $encodedPassword = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>$null
    if ($encodedPassword) {
        $password = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encodedPassword))
        Write-Host ""
        Write-Host "  ArgoCD UI : http://localhost:8080" -ForegroundColor Green
        Write-Host "  Username  : admin" -ForegroundColor Green
        Write-Host "  Password  : $password" -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not retrieve password automatically." -ForegroundColor Yellow
    Write-Host "  Run manually: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=""{.data.password}"" | base64 -d" -ForegroundColor Yellow
}

# --- Port-forward (blocking - keeps UI accessible) ---
Write-Host "`n[INFO] Starting port-forward: localhost:8080 -> argocd-server:80" -ForegroundColor Yellow
Write-Host "       Press Ctrl+C to stop." -ForegroundColor Yellow
kubectl port-forward svc/argocd-server -n argocd 8080:80