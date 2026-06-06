# Notion API Integration Guide — Project OMNI

## 1. Objectif

Ce document décrit l'intégration entre Project OMNI et l'API Notion pour :
- La synchronisation automatique de la documentation.
- La création de pages de projet et de rapports d'audit.
- Le suivi des tâches via les bases de données Notion.

## 2. Prérequis

1. Compte Notion avec accès API.
2. Token d'intégration : `NOTION_TOKEN`.
3. ID de base de données : `NOTION_DATABASE_ID`.

## 3. Configuration

```bash
# .env
NOTION_TOKEN=secret_xxx
NOTION_DATABASE_ID=your_database_id
```

## 4. Endpoints Utilisés

| Endpoint | Méthode | Usage |
|----------|---------|-------|
| `/v1/pages` | POST | Créer une page |
| `/v1/blocks/{id}/children` | PATCH | Ajouter du contenu |
| `/v1/databases/{id}` | GET | Lire la structure |

## 5. Script de Sync

Utiliser `scripts/sync-notion.sh` pour pousser automatiquement :
- `docs/architecture.md`
- `docs/security.md`
- `docs/specs.md`
- `tests/reports/resilience-report.md`

## 6. Structure du Workspace Notion

```
Project OMNI v2.0 (Page parent)
├── Architecture & DFD
├── Spécifications Techniques
├── Modèle de Sécurité
├── Rapport de Tests
└── Sprint Backlog (Database)
```

## 7. Automatisation

Dans n8n, ajouter un nœud Notion à la fin du pipeline pour créer une entrée dans la base de données à chaque tâche approuvée.
