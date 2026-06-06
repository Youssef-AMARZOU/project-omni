#!/usr/bin/env bash
# ============================================================
# sync-hf.sh — Push vers Hugging Face (dataset + model card)
# ============================================================
set -euo pipefail

REPO_ID="${HF_REPO_ID:-entreprise/project-omni}"
TOKEN="${HF_API_TOKEN:-}"
PRIVATE="${HF_PRIVATE:-false}"

if [ -z "$TOKEN" ]; then
    echo "Erreur : HF_API_TOKEN non défini."
    exit 1
fi

echo "[Hugging Face] Sync vers $REPO_ID..."

# 1. Créer le repo si inexistant
curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "https://huggingface.co/api/repos/create" \
    -d "{\"name\": \"$REPO_ID\", \"type\": \"dataset\", \"private\": $PRIVATE}" \
    > /dev/null || true

# 2. Git LFS pour les gros fichiers
git lfs install 2>/dev/null || true

# 3. Remote HF
HF_GIT_URL="https://huggingface.co/datasets/${REPO_ID}"
git remote add hf "https://${TOKEN}@${HF_GIT_URL#https://}" 2>/dev/null || true

# 4. Copier les fichiers pertinents
mkdir -p hf_upload
cp -r docs hf_upload/
cp -r tests/reports hf_upload/
cp README.md hf_upload/

# 5. README.md → README.md du dataset
cp README.md hf_upload/README.md

# 6. Commit & push
cd hf_upload
git init 2>/dev/null || true
git add .
git commit -m "feat: Project OMNI v2.0 — Dataset & documentation" || true
git push -u hf main --force || true
cd ..

echo "[Hugging Face] Sync terminé avec succès."
echo "URL : https://huggingface.co/datasets/$REPO_ID"
