#requires -Version 5.1
<#
.SYNOPSIS
    Script interactif de configuration des tokens et synchronisation.
.DESCRIPTION
    Guide l'utilisateur étape par étape pour configurer les tokens API
    et lancer la sync multi-plateformes. Pas besoin de savoir coder.
#>

function Show-Title {
    param([string]$Text)
    Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Ask-Token {
    param(
        [string]$Service,
        [string]$Description,
        [string]$Example,
        [switch]$Required
    )
    Write-Host "`n[$Service]" -ForegroundColor Yellow
    Write-Host $Description -ForegroundColor White
    Write-Host "Exemple: $Example" -ForegroundColor DarkGray
    if (-not $Required) {
        Write-Host "(Appuyez sur Entrée pour ignorer)" -ForegroundColor DarkGray
    }
    $token = Read-Host -Prompt "Votre token"
    return $token
}

function Show-Progress {
    param([string]$Text)
    Write-Host "`n  → $Text" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════
# SCRIPT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

Clear-Host
Show-Title "CONFIGURATION PROJECT OMNI - SYNC MULTI-PLATEFORMES"

Write-Host "`nCe script va vous aider à configurer les tokens API nécessaires" -ForegroundColor White
Write-Host "pour synchroniser Project OMNI avec GitHub, GitLab, Hugging Face, Jira et Notion." -ForegroundColor White
Write-Host "`nAppuyez sur Entrée pour commencer..." -ForegroundColor DarkGray
Read-Host | Out-Null

# ─── GitHub ─────────────────────────────────────────────────────────
Show-Title "1. GitHub Token (RECOMMANDÉ)"
Write-Host "Ouvrez https://github.com/settings/tokens" -ForegroundColor Blue
Write-Host "Cliquez 'Generate new token (classic)'" -ForegroundColor White
Write-Host "Cochez ✅ 'repo' puis générez" -ForegroundColor White
Write-Host "Copiez le token qui commence par ghp_" -ForegroundColor White

$github_token = Ask-Token -Service "GitHub" -Description "Token GitHub (classic) avec scope 'repo'" -Example "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# ─── GitLab ─────────────────────────────────────────────────────────
Show-Title "2. GitLab (DÉJÀ CONFIGURÉ)"
Write-Host "✅ GitLab est déjà configuré et pushé !" -ForegroundColor Green

# ─── Hugging Face ───────────────────────────────────────────────────
Show-Title "3. Hugging Face Token"
Write-Host "Ouvrez https://huggingface.co/settings/tokens" -ForegroundColor Blue
Write-Host "Cliquez 'New token' → Role: Write" -ForegroundColor White
Write-Host "Copiez le token qui commence par hf_" -ForegroundColor White

$hf_token = Ask-Token -Service "Hugging Face" -Description "Token HF avec permissions Write" -Example "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# ─── Jira ────────────────────────────────────────────────────────────
Show-Title "4. Jira (Atlassian)"
Write-Host "Ouvrez https://id.atlassian.com/manage-profile/security/api-tokens" -ForegroundColor Blue
Write-Host "Cliquez 'Create API token' → Nommez-le 'Project OMNI'" -ForegroundColor White
Write-Host "Copiez le token qui commence par ATATT..." -ForegroundColor White

$jira_url = Ask-Token -Service "Jira URL" -Description "URL de votre instance Jira" -Example "https://mon-entreprise.atlassian.net"
$jira_email = Ask-Token -Service "Jira Email" -Description "Email de connexion Jira" -Example "moi@entreprise.com"
$jira_token = Ask-Token -Service "Jira API Token" -Description "Token API Jira" -Example "ATATT3xFfGF0..."

# ─── Notion ──────────────────────────────────────────────────────────
Show-Title "5. Notion"
Write-Host "Ouvrez https://www.notion.so/my-integrations" -ForegroundColor Blue
Write-Host "Cliquez 'New integration' → Nommez-la 'Project OMNI'" -ForegroundColor White
Write-Host "Copiez le 'Internal Integration Token' qui commence par ntn_" -ForegroundColor White

$notion_token = Ask-Token -Service "Notion" -Description "Token d'intégration Notion" -Example "ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# ─── Sauvegarde .env ─────────────────────────────────────────────────
Show-Title "SAUVEGARDE DES TOKENS"

$envContent = @"
# ═══════════════════════════════════════════════════════════════════
# TOKENS PROJECT OMNI - Généré le $(Get-Date -Format "yyyy-MM-dd HH:mm")
# ═══════════════════════════════════════════════════════════════════

# GitHub
GITHUB_TOKEN=$github_token
GITHUB_REPO_OWNER=VOTRE-USERNAME
GITHUB_REPO_NAME=project-omni

# GitLab (déjà configuré)
GITLAB_TOKEN=$gitlab_token
GITLAB_PROJECT_ID=82950759
GITLAB_URL=https://gitlab.com

# Hugging Face
HF_API_TOKEN=$hf_token
HF_REPO_ID=VOTRE-USERNAME/project-omni
HF_PRIVATE=false

# Jira
JIRA_URL=$jira_url
JIRA_EMAIL=$jira_email
JIRA_API_TOKEN=$jira_token
JIRA_PROJECT_KEY=OMNI

# Notion
NOTION_TOKEN=$notion_token
NOTION_DATABASE_ID=VOTRE-DATABASE-ID

# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Databases
POSTGRES_USER=omni
POSTGRES_PASSWORD=omni_password
POSTGRES_DB=omni_n8n
MONGO_USER=omni
MONGO_PASSWORD=omni_password
MONGO_DB=omni_logs
RABBITMQ_USER=omni
RABBITMQ_PASSWORD=omni_password

# Résilience
FALLBACK_LLM_PROVIDER=anthropic
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Logging
LOG_LEVEL=INFO
OMNI_DATA_DIR=./data
"@

$envPath = Join-Path $PSScriptRoot "..\.env"
$envContent | Out-File -FilePath $envPath -Encoding UTF8

Write-Host "✅ Fichier .env créé avec succès !" -ForegroundColor Green
Write-Host "Chemin: $envPath" -ForegroundColor DarkGray

# ─── Résumé ──────────────────────────────────────────────────────────
Show-Title "RÉSUMÉ DE LA CONFIGURATION"

$services = @(
    @{ Name="GitHub"; Configured=($github_token -ne "") },
    @{ Name="GitLab"; Configured=$true },
    @{ Name="Hugging Face"; Configured=($hf_token -ne "") },
    @{ Name="Jira"; Configured=($jira_token -ne "") },
    @{ Name="Notion"; Configured=($notion_token -ne "") }
)

foreach ($svc in $services) {
    $status = if ($svc.Configured) { "✅ CONFIGURÉ" } else { "⏭️  IGNORÉ" }
    $color = if ($svc.Configured) { "Green" } else { "DarkGray" }
    Write-Host "  $($svc.Name.PadRight(15)) $status" -ForegroundColor $color
}

# ─── Lancer la sync ──────────────────────────────────────────────────
Show-Title "LANCER LA SYNCHRONISATION"

Write-Host "`nSouhaitez-vous lancer la sync maintenant ? (O/n)" -ForegroundColor Yellow
$confirm = Read-Host

if ($confirm -eq "O" -or $confirm -eq "o" -or $confirm -eq "") {
    Write-Host "`nLancement de la sync..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "sync-all.ps1")
} else {
    Write-Host "`nSync annulée. Pour relancer plus tard :" -ForegroundColor Yellow
    Write-Host "  .\scripts\sync-all.ps1" -ForegroundColor Cyan
}

Show-Title "TERMINE"
Write-Host "`nMerci d'avoir configuré Project OMNI !" -ForegroundColor Green
Write-Host "Pour toute question : youssef.amarzou@yahoo.com — Youssef AMARZOU" -ForegroundColor DarkGray
