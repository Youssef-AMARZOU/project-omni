#!/usr/bin/env bash
# ============================================================
# sync-gitlab.sh — Push OMNI vers GitLab + CI/CD + Issues
# ============================================================
set -euo pipefail

PROJECT_ID="${GITLAB_PROJECT_ID:-}"
TOKEN="${GITLAB_TOKEN:-}"
URL="${GITLAB_URL:-https://gitlab.com}"
BRANCH="${GITLAB_BRANCH:-main}"

if [ -z "$TOKEN" ] || [ -z "$PROJECT_ID" ]; then
    echo "Erreur : GITLAB_TOKEN et GITLAB_PROJECT_ID requis."
    exit 1
fi

echo "[GitLab] Sync vers projet $PROJECT_ID..."

# 1. Remote
git remote add gitlab "https://oauth2:${TOKEN}@${URL#https://}/${PROJECT_ID}.git" 2>/dev/null || true

# 2. Push
git push -u gitlab "$BRANCH" --force-with-lease

# 3. Création Issues (GitLab API)
issues=(
    'Déploiement Kubernetes'
    'Intégration monitoring'
    'Tests de chaos engineering'
)

for title in "${issues[@]}"; do
    curl -s -X POST \
        -H "PRIVATE-TOKEN: $TOKEN" \
        "${URL}/api/v4/projects/${PROJECT_ID}/issues" \
        -d "title=$title" \
        -d "labels=omni-v2,auto-generated" \
        > /dev/null && echo "[GitLab] Issue créée: $title"
done

# 4. Trigger Pipeline CI
curl -s -X POST \
    -H "PRIVATE-TOKEN: $TOKEN" \
    "${URL}/api/v4/projects/${PROJECT_ID}/pipeline" \
    -d "ref=$BRANCH" \
    > /dev/null && echo "[GitLab] Pipeline CI déclenchée."

echo "[GitLab] Sync terminé avec succès."
