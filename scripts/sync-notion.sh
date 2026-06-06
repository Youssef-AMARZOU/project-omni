#!/usr/bin/env bash
# ============================================================
# sync-notion.sh — Création workspace Notion + documentation
# ============================================================
set -euo pipefail

TOKEN="${NOTION_TOKEN:-}"
DB_ID="${NOTION_DATABASE_ID:-}"

if [ -z "$TOKEN" ]; then
    echo "Erreur : NOTION_TOKEN non défini."
    exit 1
fi

echo "[Notion] Sync documentation vers workspace..."

# 1. Création d'une page parent
parent_page=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Notion-Version: 2022-06-28" \
    -H "Content-Type: application/json" \
    "https://api.notion.com/v1/pages" \
    -d '{
      "parent": {"database_id": "'"$DB_ID"'"},
      "properties": {
        "Name": {"title": [{"text": {"content": "Project OMNI v2.0"}}]},
        "Status": {"select": {"name": "In Progress"}}
      }
    }' | jq -r '.id')

echo "[Notion] Page parent créée: $parent_page"

# 2. Ajout contenu documentation
for file in docs/architecture.md docs/security.md docs/specs.md; do
    if [ -f "$file" ]; then
        content=$(cat "$file" | sed 's/"/\\"/g' | head -c 2000)
        curl -s -X PATCH \
            -H "Authorization: Bearer $TOKEN" \
            -H "Notion-Version: 2022-06-28" \
            -H "Content-Type: application/json" \
            "https://api.notion.com/v1/blocks/$parent_page/children" \
            -d "{
              \"children\": [
                {
                  \"object\": \"block\",
                  \"type\": \"heading_2\",
                  \"heading_2\": {\"rich_text\": [{\"type\": \"text\", \"text\": {\"content\": \"$file\"}}]}
                },
                {
                  \"object\": \"block\",
                  \"type\": \"paragraph\",
                  \"paragraph\": {\"rich_text\": [{\"type\": \"text\", \"text\": {\"content\": \"$content\"}}]}
                }
              ]
            }" > /dev/null
        echo "[Notion] $file importé."
    fi
done

echo "[Notion] Sync terminé avec succès."
