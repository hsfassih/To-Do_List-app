<#
.SYNOPSIS
    Installs, upgrades, or deploys the todo-app Helm chart.

.DESCRIPTION
    Default (no flags):
        Installs the Helm chart from todo-app-chart/ using the base values.yaml.

    --ns <namespace>
        Optional in install/deploy mode. Forces target namespace and also sets
        chart value 'namespace=<namespace>' to keep resource metadata aligned.

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

# --- Argument parsing ---
$DoUpgrade = $false
$TargetNs = $null
$DeployValues = $null

for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        "--upgrade" { $DoUpgrade = $true }
        "--ns" {
            $i++
            if ($i -ge $args.Count) {
                throw "[ERROR] --ns requires a value."
            }
            $TargetNs = $args[$i]
        }
        "--deploy" {
            $i++
            if ($i -ge $args.Count) {
                throw "[ERROR] --deploy requires a values file path."
            }
            $DeployValues = $args[$i]
        }
        default {
            throw "[ERROR] Unknown argument: $($args[$i])"
        }
    }
}

# --- Validate argument combinations ---
if ($DoUpgrade -and $DeployValues) {
    throw "[ERROR] --upgrade and --deploy cannot be used together."
}
if ($DoUpgrade -and -not $TargetNs) {
    throw "[ERROR] --upgrade requires --ns <namespace>."
}

# --- Helper: resolve values file path ---
function Resolve-ValuesFilePath([string]$valuesFileInput) {
    $candidates = @()

    if ([System.IO.Path]::IsPathRooted($valuesFileInput)) {
        $candidates += $valuesFileInput
    } else {
        # Candidate 1: exactly as supplied from current working directory.
        $candidates += (Join-Path (Get-Location) $valuesFileInput)
        # Candidate 2: relative to chart path.
        $candidates += (Join-Path $ChartPath $valuesFileInput)
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "[ERROR] Values file not found. Tried: $($candidates -join ', ')"
}

# --- Helper: resolve namespace from values file ---
function Get-NamespaceFromValues([string]$valuesFilePath) {
    $ns = Get-Content -LiteralPath $valuesFilePath |
          Where-Object { $_ -match '^\s*namespace\s*:\s*(\S+)' } |
          ForEach-Object { $Matches[1] } |
          Select-Object -First 1
    if (-not $ns) { $ns = "todo-app" }
    return $ns
}

# --- Helper: run helm and fail properly on errors ---
function Invoke-HelmUpsert([string]$namespace, [string]$valuesPath) {
    $helmArgs = @(
        "upgrade", "--install", $ReleaseName, $ChartPath,
        "-n", $namespace,
        "--create-namespace",
        "--set", "namespace=$namespace"
    )

    if ($valuesPath) {
        $helmArgs += @("-f", $valuesPath)
    }

    & helm @helmArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "" 
        Write-Host "[HINT] Existing non-Helm resources can block installation." -ForegroundColor Yellow
        Write-Host "       If needed, clean namespace resources or deploy to a different namespace." -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
}

# --- Lint the chart before any operation ---
Write-Host "`n[Lint] Validating Helm chart..." -ForegroundColor Cyan
helm lint $ChartPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] Helm lint failed. Fix chart errors before deploying."
    exit 1
}

# ============================================================================
# MODE A: --upgrade --ns <namespace>
# ============================================================================
if ($DoUpgrade) {
    Write-Host "`n[Upgrade] Upgrading release '$ReleaseName' in namespace '$TargetNs'..." -ForegroundColor Cyan
    Invoke-HelmUpsert -namespace $TargetNs -valuesPath $null
    Write-Host "`n[OK] Release upgraded in namespace '$TargetNs'.`n" -ForegroundColor Green
    helm status $ReleaseName -n $TargetNs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    exit 0
}

# ============================================================================
# MODE B: --deploy <values-file> [--ns <namespace>]
# ============================================================================
if ($DeployValues) {
    $valuesPath = Resolve-ValuesFilePath $DeployValues
    $nsFromFile = Get-NamespaceFromValues $valuesPath
    $ns = if ($TargetNs) { $TargetNs } else { $nsFromFile }

    Write-Host "`n[Deploy] Deploying with '$DeployValues' into namespace '$ns'..." -ForegroundColor Cyan
    Invoke-HelmUpsert -namespace $ns -valuesPath $valuesPath
    Write-Host "`n[OK] Deployed with '$DeployValues' into namespace '$ns'.`n" -ForegroundColor Green
    helm status $ReleaseName -n $ns
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    exit 0
}

# ============================================================================
# MODE C: install with base values.yaml [--ns <namespace>]
# ============================================================================
$installNs = if ($TargetNs) { $TargetNs } else { "todo-app" }
Write-Host "`n[Install] Installing Helm chart '$ReleaseName' into namespace '$installNs'..." -ForegroundColor Cyan
Invoke-HelmUpsert -namespace $installNs -valuesPath $null
Write-Host "`n[OK] Chart installed in namespace '$installNs'.`n" -ForegroundColor Green
helm status $ReleaseName -n $installNs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
