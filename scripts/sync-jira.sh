#!/usr/bin/env bash
# ============================================================
# sync-jira.sh — Création tickets Jira à partir du CDC
# ============================================================
set -euo pipefail

JIRA_URL="${JIRA_URL:-https://entreprise.atlassian.net}"
EMAIL="${JIRA_EMAIL:-}"
TOKEN="${JIRA_API_TOKEN:-}"
PROJECT="${JIRA_PROJECT_KEY:-OMNI}"

if [ -z "$TOKEN" ]; then
    echo "Erreur : JIRA_API_TOKEN non défini."
    exit 1
fi

echo "[Jira] Création des tickets de projet..."

issues_payload='[
  {"fields": {"project": {"key": "'"$PROJECT"'"}, "summary": "[OMNI] Architecture Kubernetes — Déploiement", "description": "Déploiement de la stack OMNI sur cluster K8s avec Helm charts.", "issuetype": {"name": "Task"}}},
  {"fields": {"project": {"key": "'"$PROJECT"'"}, "summary": "[OMNI] Intégration Prometheus & Grafana", "description": "Dashboards de monitoring pour les SLAs 99.9%.", "issuetype": {"name": "Task"}}},
  {"fields": {"project": {"key": "'"$PROJECT"'"}, "summary": "[OMNI] Tests de résilience — Chaos Engineering", "description": "Injection de pannes pour valider le Circuit Breaker.", "issuetype": {"name": "Task"}}},
  {"fields": {"project": {"key": "'"$PROJECT"'"}, "summary": "[OMNI] RAG — Indexation historique SAP", "description": "Intégration des données historiques dans Qdrant.", "issuetype": {"name": "Story"}}}
]'

echo "$issues_payload" | jq -c '.[]' | while read -r issue; do
    curl -s -X POST \
        -u "${EMAIL}:${TOKEN}" \
        -H "Content-Type: application/json" \
        "${JIRA_URL}/rest/api/3/issue" \
        -d "$issue" > /dev/null && echo "[Jira] Ticket créé."
done

echo "[Jira] Sync terminé avec succès."
