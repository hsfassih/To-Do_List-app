<#
.SYNOPSIS
    Installs, upgrades, or deploys the todo-app Helm chart.

.DESCRIPTION
    Default (no flags):
        Installs the Helm chart from todo-app-chart/ using the base values.yaml.

    --upgrade --ns <namespace>
        Upgrades the existing Helm release in the given namespace.
        Example: .\SetHelm.ps1 --upgrade --ns todo-local

    --deploy <values-file>
        Deploys (install or upgrade) the chart using the specified values file.
        The values file should exist inside todo-app-chart/ (e.g. values-dev.yaml).
        The namespace is read from the values file's 'namespace' key; falls back to todo-app.
        Example: .\SetHelm.ps1 --deploy values-dev.yaml
        Example: .\SetHelm.ps1 --deploy values-prod.yaml

.NOTES
    Requires: helm, kubectl
    All operations are idempotent (uses --install on upgrade).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ChartPath   = "./todo-app-chart"
$ReleaseName = "todo-app"

# ── Argument parsing ──────────────────────────────────────────────────────────
$DoUpgrade = $false
$UpgradeNs = $null
$DeployValues = $null

for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        "--upgrade" { $DoUpgrade = $true }
        "--ns"      { $i++; $UpgradeNs = $args[$i] }
        "--deploy"  { $i++; $DeployValues = $args[$i] }
    }
}

# ── Validate conflicting flags ────────────────────────────────────────────────
if ($DoUpgrade -and $DeployValues) {
    Write-Error "[ERROR] --upgrade and --deploy cannot be used together."
    exit 1
}
if ($DoUpgrade -and -not $UpgradeNs) {
    Write-Error "[ERROR] --upgrade requires --ns <namespace>."
    exit 1
}

# ── Helper: resolve namespace from a values file ──────────────────────────────
function Get-NamespaceFromValues([string]$valuesFile) {
    $fullPath = Join-Path $ChartPath $valuesFile
    if (-not (Test-Path $fullPath)) {
        Write-Error "[ERROR] Values file not found: $fullPath"
        exit 1
    }
    $ns = Get-Content $fullPath |
          Where-Object { $_ -match '^\s*namespace\s*:\s*(\S+)' } |
          ForEach-Object { $Matches[1] } |
          Select-Object -First 1
    if (-not $ns) { $ns = "todo-app" }
    return $ns
}

# ── Lint the chart before any operation ───────────────────────────────────────
Write-Host "`n[Lint] Validating Helm chart..." -ForegroundColor Cyan
helm lint $ChartPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] Helm lint failed. Fix chart errors before deploying."
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE A: --upgrade --ns <namespace>
# ─────────────────────────────────────────────────────────────────────────────
if ($DoUpgrade) {
    Write-Host "`n[Upgrade] Upgrading release '$ReleaseName' in namespace '$UpgradeNs'..." -ForegroundColor Cyan
    helm upgrade --install $ReleaseName $ChartPath `
        -n $UpgradeNs `
        --create-namespace
    Write-Host "`n[OK] Release upgraded in namespace '$UpgradeNs'.`n" -ForegroundColor Green
    helm status $ReleaseName -n $UpgradeNs
    exit 0
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE B: --deploy <values-file>
# ─────────────────────────────────────────────────────────────────────────────
if ($DeployValues) {
    $valuesPath = Join-Path $ChartPath $DeployValues
    if (-not (Test-Path $valuesPath)) {
        Write-Error "[ERROR] Values file not found: $valuesPath"
        exit 1
    }
    $ns = Get-NamespaceFromValues $DeployValues
    Write-Host "`n[Deploy] Deploying with '$DeployValues' into namespace '$ns'..." -ForegroundColor Cyan
    helm upgrade --install $ReleaseName $ChartPath `
        -n $ns `
        --create-namespace `
        -f $valuesPath
    Write-Host "`n[OK] Deployed with '$DeployValues' into namespace '$ns'.`n" -ForegroundColor Green
    helm status $ReleaseName -n $ns
    exit 0
}

# ─────────────────────────────────────────────────────────────────────────────
# MODE C: default install with base values.yaml
# ─────────────────────────────────────────────────────────────────────────────
$defaultNs = "todo-app"
Write-Host "`n[Install] Installing Helm chart '$ReleaseName' into namespace '$defaultNs'..." -ForegroundColor Cyan
helm upgrade --install $ReleaseName $ChartPath `
    -n $defaultNs `
    --create-namespace
Write-Host "`n[OK] Chart installed in namespace '$defaultNs'.`n" -ForegroundColor Green
helm status $ReleaseName -n $defaultNs
