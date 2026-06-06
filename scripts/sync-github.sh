#!/usr/bin/env bash
# ============================================================
# sync-github.sh — Push OMNI vers GitHub + Issues + Actions
# ============================================================
set -euo pipefail

REPO="${GITHUB_REPO:-${GITHUB_REPO_OWNER:-entreprise}/${GITHUB_REPO_NAME:-project-omni}}"
TOKEN="${GITHUB_TOKEN:-}"
BRANCH="${GITHUB_BRANCH:-main}"

if [ -z "$TOKEN" ]; then
    echo "Erreur : GITHUB_TOKEN non défini."
    exit 1
fi

echo "[GitHub] Sync vers $REPO..."

# 1. Init / remote
git init 2>/dev/null || true
git remote add origin "https://${TOKEN}@github.com/${REPO}.git" 2>/dev/null || true

# 2. Commit
git add .
git commit -m "feat(omni): v2.0.0 — Multi-Agent ETL Orchestration Engine" || true

# 3. Push
git push -u origin "$BRANCH" --force-with-lease

# 4. Création Issues standards
issues=(
    'feat: Déploiement Kubernetes production'
    'feat: Intégration Prometheus + Grafana'
    'feat: Chaos Engineering tests'
    'feat: Auto-scaling Qdrant cluster'
    'docs: ADR-004 — Choix Kafka vs RabbitMQ'
)

for title in "${issues[@]}"; do
    curl -s -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/${REPO}/issues" \
        -d "{\"title\": \"$title\", \"labels\": [\"auto-generated\", \"omni-v2\"]}" \
        > /dev/null && echo "[GitHub] Issue créée: $title"
done

# 5. Vérification Actions
sleep 5
curl -s -H "Authorization: token $TOKEN" \
    "https://api.github.com/repos/${REPO}/actions/runs" | \
    grep -q '"total_count"' && echo "[GitHub] Actions workflow détecté."

echo "[GitHub] Sync terminé avec succès."
