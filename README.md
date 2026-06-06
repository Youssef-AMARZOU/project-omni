---
title: Project OMNI
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
sdk_version: "3.11"
app_file: src/main.py
pinned: false
---

# OMNI Enterprise - Multi-Agent ETL Orchestration Engine

> **Project OMNI** — Système Multi-Agents d'Orchestration et d'Optimisation des Opérations
> 
> Architecture Event-Driven, RAG Vectorielle, Haute Disponibilité 99.9%

---

## 1. Vue d'ensemble

Project OMNI est une plateforme d'orchestration de données d'entreprise conçue selon les standards Industrie 4.0. Elle intègre :

- **Routage Sémantique Intelligent** : Classification automatique des flux (Critique, Standard, Complexe).
- **Mémoire Contextuelle (RAG)** : Base vectorielle Qdrant pour l'enrichissement historique des tâches.
- **Multi-Agents Spécialisés** : Extracteur, Planificateur, Validateur avec boucle de rétroaction.
- **Résilience Enterprise** : Circuit Breakers, Fallback LLM, Graceful Degradation.
- **Traçabilité Totale** : Logs immuables dans MongoDB avec audit complet des décisions IA.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     COUCHE INGESTION                        │
│  Webhooks • CDC • RabbitMQ / Kafka • Event Listeners       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  ORCHESTRATEUR n8n                          │
│  Workflow Engine • Event Triggers • Error Handling Nodes   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──┐  ┌──────▼───┐  ┌────▼─────┐
│  Agent   │  │  Agent   │  │  Agent   │
│ Extracteur│  │ Planificateur│  │ Validateur│
└─────┬────┘  └─────┬────┘  └────┬─────┘
      │             │            │
      └─────────────┴────────────┘
                    │
         ┌──────────▼──────────┐
         │   COUCHE MÉMOIRE    │
         │  Qdrant Vector DB   │
         │   (Embeddings RAG)  │
         └──────────┬──────────┘
                    │
      ┌─────────────┼─────────────┐
      │             │             │
┌─────▼────┐  ┌─────▼────┐  ┌────▼────┐
│ PostgreSQL│  │ MongoDB  │  │  ERP /  │
│  (SQL)   │  │ (Logs)   │  │  API    │
└──────────┘  └──────────┘  └─────────┘
```

---

## 3. Démarrage Rapide

### 3.1 Prérequis

- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+ (pour le développement local)
- Clés API : OpenAI, Anthropic (optionnel)

### 3.2 Installation

```bash
# 1. Clone
git clone https://github.com/Youssef-AMARZOU/project-omni.git
cd project-omni-enterprise

# 2. Configuration
cp .env.example .env
# Éditez .env avec vos secrets

# 3. Lancement complet
 docker-compose up -d

# 4. Vérification
 docker-compose ps
 curl http://localhost:5678/healthz   # n8n
 curl http://localhost:6333/healthz   # Qdrant
```

### 3.3 Accès aux Services

| Service | URL | Identifiants |
|---------|-----|--------------|
| n8n | http://localhost:5678 | `.env` N8N_BASIC_AUTH_* |
| Qdrant | http://localhost:6333 | - |
| PostgreSQL | localhost:5432 | `.env` POSTGRES_* |
| MongoDB | localhost:27017 | `.env` MONGO_* |
| RabbitMQ Management | http://localhost:15672 | `.env` RABBITMQ_* |

---

## 4. Structure du Projet

```
project-omni-enterprise/
├── docker-compose.yml           # Stack complet
├── .env.example                 # Template de secrets
├── README.md                    # Ce fichier
├── Makefile                     # Commandes de build
│
├── docker/
│   └── Dockerfile.agents        # Image Python des agents
│
├── src/
│   ├── main.py                  # Point d'entrée
│   ├── requirements.txt         # Dépendances Python
│   ├── agents/
│   │   ├── extractor.py         # Nettoyage & schéma strict
│   │   ├── planner.py           # Optimisation sous contraintes
│   │   └── validator.py         # Audit & boucle de correction
│   ├── orchestrator/
│   │   └── workflow_engine.py # Coordination event-driven
│   ├── rag/
│   │   ├── vector_store.py      # Interface Qdrant
│   │   └── embeddings.py        # Génération d'embeddings
│   └── utils/
│       ├── config.py            # Pydantic settings
│       ├── logger.py            # Structured logging → MongoDB
│       ├── fallback.py          # Fallback LLM & retry
│       └── circuit_breaker.py   # Circuit breaker pattern
│
├── n8n-workflows/
│   ├── semantic-router.json     # Routage sémantique
│   ├── etl-pipeline.json        # Pipeline ETL complet
│   └── error-handling.json      # Gestion des erreurs & fallback
│
├── docs/
│   ├── architecture.md          # Architecture détaillée (Mermaid)
│   ├── data-flow-diagram.md     # DFD niveau 0, 1, 2
│   ├── security.md              # Modèle de sécurité & audit
│   ├── api-reference.md         # API internes
│   └── specs.md                 # Spécifications techniques
│
├── tests/
│   ├── test_resilience.py       # Tests de panne API
│   ├── test_agents.py           # Tests unitaires agents
│   └── reports/
│       └── resilience-report.md # Rapport de résilience
│
├── scripts/
│   ├── deploy.sh                # Déploiement cloud
│   ├── sync-github.sh           # Sync vers GitHub
│   ├── sync-gitlab.sh           # Sync vers GitLab
│   ├── sync-jira.sh             # Sync issues Jira
│   ├── sync-notion.sh           # Sync docs Notion
│   └── sync-hf.sh               # Sync Hugging Face
│
├── .github/workflows/
│   └── ci.yml                   # CI/CD GitHub Actions
│
├── .gitlab/
│   └── .gitlab-ci.yml           # CI/CD GitLab
│
├── notion/
│   └── notion-api-integration.md # Guide Notion
│
└── huggingface/
    └── README.md                # Carte HF du dataset/modèle
```

---

## 5. Agents

### 5.1 Agent Extracteur
- **Rôle** : Nettoyage de la donnée brute, validation schéma, sanitization PII.
- **Entrée** : JSON brut / Webhook / CDC.
- **Sortie** : Payload structuré conforme au schéma OMNI.
- **Fichier** : `src/agents/extractor.py`

### 5.2 Agent Planificateur
- **Rôle** : Optimisation sous contraintes métier, allocation ressources.
- **Entrée** : Tâche structurée + contexte RAG.
- **Sortie** : Planning détaillé avec estimation de charge.
- **Fichier** : `src/agents/planner.py`

### 5.3 Agent Validateur
- **Rôle** : Audit de la sortie planificateur, détection d'anomalies.
- **Entrée** : Plan généré.
- **Sortie** : Plan approuvé ou retour avec message d'erreur.
- **Fichier** : `src/agents/validator.py`

---

## 6. Résilience & Sécurité

### 6.1 Graceful Degradation
Si OpenAI retourne 429/500 :
1. **Error Trigger** n8n capture l'erreur.
2. **Switch conditionnel** bascule vers Anthropic Claude.
3. **Alerte** loggée dans MongoDB sans interruption.

### 6.2 Circuit Breaker
- Seuil : 5 erreurs consécutives.
- Timeout : 60 secondes.
- Fallback : modèle local ou file d'attente manuelle.

### 6.3 Sécurité
- **Sanitization** : PII masquée avant envoi aux LLM externes.
- **Secrets** : Variables d'environnement uniquement (jamais en dur).
- **Audit** : Chaque décision IA est loggée (entrée, prompt, sortie, confiance).

---

## 7. Tests de Résilience

```bash
# Simulation de panne API
python -m pytest tests/test_resilience.py -v

# Rapport généré
 cat tests/reports/resilience-report.md
```

---

## 8. Livrables

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Architecture Documentée | `docs/architecture.md` | ✅ |
| Data Flow Diagram | `docs/data-flow-diagram.md` | ✅ |
| Scripts Docker | `docker-compose.yml` | ✅ |
| Dépôt Code | Ce repo | ✅ |
| Tests de Résilience | `tests/reports/resilience-report.md` | ✅ |
| CI/CD | `.github/workflows/ci.yml` | ✅ |

---

## 9. Plateformes

| Plateforme | Lien |
|-----------|------|
| GitHub | https://github.com/Youssef-AMARZOU/project-omni |
| GitLab | https://gitlab.com/Youssef-AMARZOU/project-omni |
| HuggingFace | https://huggingface.co/spaces/YsfMO98/YsfMO98 |
| Jira | https://syoussefama.atlassian.net/browse/INGBI |
| Notion | Project OMNI v2.0 |

---

## 10. Gouvernance

**Contact** : youssef.amarzou@yahoo.com — Youssef AMARZOU

---

*Built with intelligence. Powered by agents. Orchestrated by OMNI.*
