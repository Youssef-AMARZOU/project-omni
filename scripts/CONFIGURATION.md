# Guide de Configuration — Multi-Platform Sync

## 1. Prérequis

Avant de lancer la synchronisation, vous devez disposer des tokens et identifiants suivants :

| Service | Token / ID | Où l'obtenir |
|---------|-----------|-------------|
| **GitHub** | `GITHUB_TOKEN` (classic, scope `repo`) | Settings > Developer settings > Personal access tokens |
| **GitLab** | `GITLAB_TOKEN` (scope `api`) | User Settings > Access Tokens |
| **Jira** | `JIRA_API_TOKEN` | Account Settings > Security > API tokens |
| **Notion** | `NOTION_TOKEN` (integration token) | notion.so/my-integrations |
| **Hugging Face** | `HF_API_TOKEN` (Write access) | Settings > Access Tokens |

## 2. Configuration rapide

Copiez le fichier `.env.example` vers `.env` et remplissez les valeurs :

```bash
cp .env.example .env
# Éditez .env avec vos secrets
```

## 3. Exécution de la sync

### Windows (PowerShell)

```powershell
# Mode simulation (sans push)
.\scripts\sync-all.ps1 -DryRun

# Sync réel (tous les services)
.\scripts\sync-all.ps1

# Sync seul GitHub
.\scripts\sync-all.ps1 -GitHub

# Sync GitHub + Jira
.\scripts\sync-all.ps1 -GitHub -Jira
```

### Linux / macOS (Bash)

```bash
# GitHub
export GITHUB_TOKEN=ghp_xxx
bash scripts/sync-github.sh

# GitLab
export GITLAB_TOKEN=glpat-xxx
export GITLAB_PROJECT_ID=12345678
bash scripts/sync-gitlab.sh

# Jira
export JIRA_API_TOKEN=xxx
export JIRA_EMAIL=tech@entreprise.com
bash scripts/sync-jira.sh

# Notion
export NOTION_TOKEN=secret_xxx
bash scripts/sync-notion.sh

# Hugging Face
export HF_API_TOKEN=hf_xxx
bash scripts/sync-hf.sh
```

## 4. Vérification

Après la sync, vérifiez les URLs :

- **GitHub** : `https://github.com/<owner>/<repo>`
- **GitLab** : `https://gitlab.com/<project_id>`
- **Jira** : `https://<domain>.atlassian.net/projects/<OMNI>`
- **Notion** : Votre workspace Notion
- **Hugging Face** : `https://huggingface.co/datasets/<repo_id>`

## 5. Dépannage

### Encodage PowerShell
Si vous rencontrez des erreurs d'encodage avec les scripts `.sh` sur Windows, utilisez **exclusivement** `sync-all.ps1`.

### Git push rejected
```bash
git remote -v
git remote set-url origin https://<token>@github.com/<owner>/<repo>.git
```

### Rate limit API
Les scripts incluent des délais courts entre les appels. Si vous dépassez les limites, patientez 1 minute et relancez.

---

*Pour toute question : youssef.amarzou@yahoo.com — Youssef AMARZOU*
