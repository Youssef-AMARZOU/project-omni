#requires -Version 5.1
<#
.SYNOPSIS
    Multi-platform sync script for Project OMNI Enterprise.
.DESCRIPTION
    Pushes the project to GitHub, GitLab, Jira, Notion, and Hugging Face.
    Requires environment variables from .env file.
#>

param(
    [switch]$DryRun,
    [switch]$GitHub,
    [switch]$GitLab,
    [switch]$Jira,
    [switch]$Notion,
    [switch]$HuggingFace
)

if (-not ($GitHub -or $GitLab -or $Jira -or $Notion -or $HuggingFace)) {
    $GitHub = $GitLab = $Jira = $Notion = $HuggingFace = $true
}

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

# --- GitHub ---
if ($GitHub) {
    Write-Host "`n[GitHub] Sync..." -ForegroundColor Cyan
    $token = $env:GITHUB_TOKEN
    $owner = $env:GITHUB_REPO_OWNER -or "entreprise"
    $repo  = $env:GITHUB_REPO_NAME -or "project-omni"
    $fullRepo = "$owner/$repo"

    if ($token) {
        if ($DryRun) { Write-Host "[DRYRUN] git push github" }
        else {
            try {
                git remote add origin "https://${token}@github.com/${fullRepo}.git" 2>$null
                git push -u origin master --force-with-lease
                Write-Host "[GitHub] Push OK" -ForegroundColor Green

                $headers = @{ Authorization = "token $token"; Accept = "application/vnd.github.v3+json" }
                $issues = @(
                    "feat: Kubernetes deployment",
                    "feat: Prometheus + Grafana integration",
                    "feat: Chaos Engineering tests",
                    "feat: Qdrant auto-scaling",
                    "docs: ADR-004 - Kafka vs RabbitMQ"
                )
                foreach ($title in $issues) {
                    $body = @{ title = $title; labels = @("auto-generated","omni-v2") } | ConvertTo-Json -Depth 3
                    Invoke-RestMethod -Uri "https://api.github.com/repos/${fullRepo}/issues" -Method POST -Headers $headers -Body $body | Out-Null
                    Write-Host "  [GitHub] Issue created: $title" -ForegroundColor DarkGray
                }
            } catch { Write-Warning "[GitHub] Error: $_" }
        }
    } else { Write-Warning "GITHUB_TOKEN missing. Skipping." }
}

# --- GitLab ---
if ($GitLab) {
    Write-Host "`n[GitLab] Sync..." -ForegroundColor Cyan
    $token = $env:GITLAB_TOKEN
    $projectId = $env:GITLAB_PROJECT_ID
    $url = $env:GITLAB_URL -or "https://gitlab.com"

    if ($token -and $projectId) {
        if ($DryRun) { Write-Host "[DRYRUN] git push gitlab" }
        else {
            try {
                git remote add gitlab "https://oauth2:${token}@${url.TrimStart('https://')}/${projectId}.git" 2>$null
                git push -u gitlab master --force-with-lease
                Write-Host "[GitLab] Push OK" -ForegroundColor Green

                Invoke-RestMethod -Uri "${url}/api/v4/projects/${projectId}/pipeline" -Method POST -Headers @{ "PRIVATE-TOKEN" = $token } -Body @{ ref = "master" } | Out-Null
                Write-Host "[GitLab] Pipeline triggered" -ForegroundColor Green
            } catch { Write-Warning "[GitLab] Error: $_" }
        }
    } else { Write-Warning "GITLAB_TOKEN or GITLAB_PROJECT_ID missing. Skipping." }
}

# --- Jira ---
if ($Jira) {
    Write-Host "`n[Jira] Sync..." -ForegroundColor Cyan
    $token = $env:JIRA_API_TOKEN
    $email = $env:JIRA_EMAIL
    $jiraUrl = $env:JIRA_URL
    $project = $env:JIRA_PROJECT_KEY -or "OMNI"

    if ($token) {
        if ($DryRun) { Write-Host "[DRYRUN] create Jira tickets" }
        else {
            $issues = @(
                @{ summary = "[OMNI] Kubernetes deployment"; description = "Deploy OMNI stack on K8s with Helm."; issuetype = @{ name = "Task" } },
                @{ summary = "[OMNI] Prometheus + Grafana integration"; description = "Monitoring dashboards for 99.9% SLA."; issuetype = @{ name = "Task" } },
                @{ summary = "[OMNI] Chaos Engineering tests"; description = "Fault injection to validate Circuit Breaker."; issuetype = @{ name = "Task" } },
                @{ summary = "[OMNI] RAG - SAP historical indexing"; description = "Import historical data into Qdrant."; issuetype = @{ name = "Story" } }
            )

            $basicAuth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${email}:${token}"))
            $headers = @{ Authorization = "Basic $basicAuth"; "Content-Type" = "application/json" }

            foreach ($issue in $issues) {
                $body = @{ fields = ($issue + @{ project = @{ key = $project } }) } | ConvertTo-Json -Depth 5
                try {
                    Invoke-RestMethod -Uri "${jiraUrl}/rest/api/3/issue" -Method POST -Headers $headers -Body $body | Out-Null
                    Write-Host "  [Jira] Ticket created: $($issue.summary)" -ForegroundColor DarkGray
                } catch { Write-Warning "[Jira] Error creating ticket: $_" }
            }
            Write-Host "[Jira] Sync done" -ForegroundColor Green
        }
    } else { Write-Warning "JIRA_API_TOKEN missing. Skipping." }
}

# --- Notion ---
if ($Notion) {
    Write-Host "`n[Notion] Sync..." -ForegroundColor Cyan
    $token = $env:NOTION_TOKEN
    $dbId = $env:NOTION_DATABASE_ID

    if ($token) {
        if ($DryRun) { Write-Host "[DRYRUN] push Notion" }
        else {
            try {
                $page = @{
                    parent = @{ database_id = $dbId }
                    properties = @{
                        Name = @{ title = @(@{ text = @{ content = "Project OMNI v2.0" } }) }
                        Status = @{ select = @{ name = "In Progress" } }
                    }
                } | ConvertTo-Json -Depth 5

                $headers = @{ Authorization = "Bearer $token"; "Notion-Version" = "2022-06-28"; "Content-Type" = "application/json" }
                $resp = Invoke-RestMethod -Uri "https://api.notion.com/v1/pages" -Method POST -Headers $headers -Body $page
                Write-Host "[Notion] Parent page created: $($resp.id)" -ForegroundColor Green
            } catch { Write-Warning "[Notion] Error: $_" }
        }
    } else { Write-Warning "NOTION_TOKEN missing. Skipping." }
}

# --- Hugging Face ---
if ($HuggingFace) {
    Write-Host "`n[HuggingFace] Sync..." -ForegroundColor Cyan
    $token = $env:HF_API_TOKEN
    $repoId = $env:HF_REPO_ID -or "entreprise/project-omni"
    $private = $env:HF_PRIVATE -eq "true"

    if ($token) {
        if ($DryRun) { Write-Host "[DRYRUN] push HF" }
        else {
            try {
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
                git add . | Out-Null
                git commit -m "feat: Project OMNI v2.0" 2>$null | Out-Null
                git push -u hf master --force 2>$null | Out-Null
                Set-Location $ProjectRoot
                Write-Host "[HuggingFace] Push OK: $hfUrl" -ForegroundColor Green
            } catch { Write-Warning "[HuggingFace] Error: $_" }
        }
    } else { Write-Warning "HF_API_TOKEN missing. Skipping." }
}

Write-Host "`n[SYNC] All services processed." -ForegroundColor Cyan
Write-Host "Check warnings above for services requiring credentials." -ForegroundColor Yellow
