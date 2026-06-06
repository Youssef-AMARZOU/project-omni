#requires -Version 5.1
<#
.SYNOPSIS
    Script de synchronisation multi-plateforme — Project OMNI Enterprise.
.DESCRIPTION
    Pousse le projet vers GitHub, GitLab, Jira, Notion et Hugging Face.
    Nécessite les variables d'environnement configurées dans .env.
#>

param(
    [switch]$DryRun,
    [switch]$GitHub,
    [switch]$GitLab,
    [switch]$Jira,
    [switch]$Notion,
    [switch]$HuggingFace
)

# Si aucun switch n'est spécifié, on sync tout
if (-not ($GitHub -or $GitLab -or $Jira -or $Notion -or $HuggingFace)) {
    $GitHub = $GitLab = $Jira = $Notion = $HuggingFace = $true
}

# Charger .env
$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+?)\s*=\s*(.*?)\s*$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

# ─── GitHub ────────────────────────────────────────────────
if ($GitHub) {
    Write-Host "`n[GitHub] Synchronisation..." -ForegroundColor Cyan
    $token = $env:GITHUB_TOKEN
    $owner = $env:GITHUB_REPO_OWNER -or "entreprise"
    $repo  = $env:GITHUB_REPO_NAME -or "project-omni"
    $fullRepo = "$owner/$repo"

    if (-not $token) { Write-Warning "GITHUB_TOKEN manquant. Skipping."; continue }
    if ($DryRun) { Write-Host "[DRYRUN] git push github"; continue }

    try {
        git remote add origin "https://${token}@github.com/${fullRepo}.git" 2>$null
        git push -u origin master --force-with-lease
        Write-Host "[GitHub] Push OK" -ForegroundColor Green

        # Issues
        $issues = @(
            "feat: Déploiement Kubernetes production",
            "feat: Intégration Prometheus + Grafana",
            "feat: Chaos Engineering tests",
            "feat: Auto-scaling Qdrant cluster",
            "docs: ADR-004 — Choix Kafka vs RabbitMQ"
        )
        foreach ($title in $issues) {
            $body = @{ title = $title; labels = @("auto-generated","omni-v2") } | ConvertTo-Json -Depth 3
            Invoke-RestMethod -Uri "https://api.github.com/repos/${fullRepo}/issues" -Method POST -Headers @{
                Authorization = "token $token"
                Accept = "application/vnd.github.v3+json"
            } -Body $body | Out-Null
            Write-Host "  [GitHub] Issue créée: $title" -ForegroundColor DarkGray
        }
    } catch { Write-Warning "[GitHub] Erreur: $_" }
}

# ─── GitLab ────────────────────────────────────────────────
if ($GitLab) {
    Write-Host "`n[GitLab] Synchronisation..." -ForegroundColor Cyan
    $token = $env:GITLAB_TOKEN
    $projectId = $env:GITLAB_PROJECT_ID
    $url = $env:GITLAB_URL -or "https://gitlab.com"

    if (-not $token -or -not $projectId) { Write-Warning "GITLAB_TOKEN ou GITLAB_PROJECT_ID manquant. Skipping."; continue }
    if ($DryRun) { Write-Host "[DRYRUN] git push gitlab"; continue }

    try {
        git remote add gitlab "https://oauth2:${token}@${url.TrimStart('https://')}/${projectId}.git" 2>$null
        git push -u gitlab master --force-with-lease
        Write-Host "[GitLab] Push OK" -ForegroundColor Green

        # Trigger CI
        Invoke-RestMethod -Uri "${url}/api/v4/projects/${projectId}/pipeline" -Method POST -Headers @{ "PRIVATE-TOKEN" = $token } -Body @{ ref = "master" } | Out-Null
        Write-Host "[GitLab] Pipeline déclenchée" -ForegroundColor Green
    } catch { Write-Warning "[GitLab] Erreur: $_" }
}

# ─── Jira ────────────────────────────────────────────────
if ($Jira) {
    Write-Host "`n[Jira] Synchronisation..." -ForegroundColor Cyan
    $token = $env:JIRA_API_TOKEN
    $email = $env:JIRA_EMAIL
    $jiraUrl = $env:JIRA_URL
    $project = $env:JIRA_PROJECT_KEY -or "OMNI"

    if (-not $token) { Write-Warning "JIRA_API_TOKEN manquant. Skipping."; continue }
    if ($DryRun) { Write-Host "[DRYRUN] création tickets Jira"; continue }

    $issues = @(
        @{ summary = "[OMNI] Architecture Kubernetes — Déploiement"; description = "Déploiement de la stack OMNI sur cluster K8s avec Helm charts."; issuetype = @{ name = "Task" } },
        @{ summary = "[OMNI] Intégration Prometheus & Grafana"; description = "Dashboards de monitoring pour les SLAs 99.9%."; issuetype = @{ name = "Task" } },
        @{ summary = "[OMNI] Tests de résilience — Chaos Engineering"; description = "Injection de pannes pour valider le Circuit Breaker."; issuetype = @{ name = "Task" } },
        @{ summary = "[OMNI] RAG — Indexation historique SAP"; description = "Intégration des données historiques dans Qdrant."; issuetype = @{ name = "Story" } }
    )

    foreach ($issue in $issues) {
        $body = @{ fields = ($issue + @{ project = @{ key = $project } }) } | ConvertTo-Json -Depth 5
        try {
            Invoke-RestMethod -Uri "${jiraUrl}/rest/api/3/issue" -Method POST -Headers @{ Authorization = "Basic $([Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${email}:${token}")))" } -ContentType "application/json" -Body $body | Out-Null
            Write-Host "  [Jira] Ticket créé: $($issue.summary)" -ForegroundColor DarkGray
        } catch { Write-Warning "[Jira] Erreur création ticket: $_" }
    }
    Write-Host "[Jira] Sync terminée" -ForegroundColor Green
}

# ─── Notion ────────────────────────────────────────────────
if ($Notion) {
    Write-Host "`n[Notion] Synchronisation..." -ForegroundColor Cyan
    $token = $env:NOTION_TOKEN
    $dbId = $env:NOTION_DATABASE_ID

    if (-not $token) { Write-Warning "NOTION_TOKEN manquant. Skipping."; continue }
    if ($DryRun) { Write-Host "[DRYRUN] push Notion"; continue }

    try {
        $page = @{
            parent = @{ database_id = $dbId }
            properties = @{
                Name = @{ title = @(@{ text = @{ content = "Project OMNI v2.0" } }) }
                Status = @{ select = @{ name = "In Progress" } }
            }
        } | ConvertTo-Json -Depth 5

        $resp = Invoke-RestMethod -Uri "https://api.notion.com/v1/pages" -Method POST -Headers @{
            Authorization = "Bearer $token"
            "Notion-Version" = "2022-06-28"
            "Content-Type" = "application/json"
        } -Body $page
        Write-Host "[Notion] Page parent créée: $($resp.id)" -ForegroundColor Green
    } catch { Write-Warning "[Notion] Erreur: $_" }
}

# ─── Hugging Face ────────────────────────────────────────────────
if ($HuggingFace) {
    Write-Host "`n[HuggingFace] Synchronisation..." -ForegroundColor Cyan
    $token = $env:HF_API_TOKEN
    $repoId = $env:HF_REPO_ID -or "entreprise/project-omni"
    $private = $env:HF_PRIVATE -eq "true"

    if (-not $token) { Write-Warning "HF_API_TOKEN manquant. Skipping."; continue }
    if ($DryRun) { Write-Host "[DRYRUN] push HF"; continue }

    try {
        # Créer repo si inexistant
        $body = @{ name = $repoId; type = "dataset"; private = $private } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://huggingface.co/api/repos/create" -Method POST -Headers @{ Authorization = "Bearer $token" } -Body $body | Out-Null
    } catch { }

    try {
        $hfUrl = "https://huggingface.co/datasets/$repoId"
        git remote add hf "https://${token}@${hfUrl.TrimStart('https://')}" 2>$null

        New-Item -ItemType Directory -Path "hf_upload" -Force | Out-Null
        Copy-Item -Recurse -Path "docs","tests\reports","README.md" -Destination "hf_upload" -Force
        Set-Location "hf_upload"
        git init 2>$null | Out-Null
        git add .
        git commit -m "feat: Project OMNI v2.0" 2>$null | Out-Null
        git push -u hf master --force 2>$null | Out-Null
        Set-Location $ProjectRoot
        Write-Host "[HuggingFace] Push OK: $hfUrl" -ForegroundColor Green
    } catch { Write-Warning "[HuggingFace] Erreur: $_" }
}

Write-Host "`n[SYNC] Tous les services ont été traités." -ForegroundColor Cyan
Write-Host "Consultez les warnings ci-dessus pour les services qui nécessitent des credentials." -ForegroundColor Yellow
