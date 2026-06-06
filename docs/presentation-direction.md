# Presentation — Direction Technique

## Project OMNI v2.0

### Système Multi-Agents d'Orchestration et d'Optimisation

**Date** : Juin 2026
**Présentateur** : OMNI Engineering Team
**Classification** : Direction Technique

---

## Slide 1 — Vision

**Au-delà de l'automatisation linéaire**

> Construire un système résilient capable de raisonnement dynamique, d'optimisation des pipelines ETL, et de gestion autonome des erreurs.

**Ambition** : Industrie 4.0 — Enterprise Data Hub

---

## Slide 2 — Le Problème

### Les limites des systèmes actuels

| Problème | Conséquence |
|----------|-------------|
| Automatisation statique | Pas d'adaptation au contexte |
| Défaillance API = interruption | Perte de productivité |
| Estimations irréalistes | Retards de livraison |
| Architecture monolithique | Difficulté à scaler |
| Pas d'audit IA | Opacité des décisions |

---

## Slide 3 — La Solution

### Project OMNI — Architecture Event-Driven

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   WEBHOOK   │────▶│   n8n       │────▶│  EXTRACTOR  │
│   CDC       │     │  ORCH.      │     │   AGENT     │
│   RabbitMQ  │     │             │     │  (PII/LLM)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                        ┌───────────────────────┼─────────────┐
                        │                       │             │
                   ┌────▼────┐           ┌─────▼────┐  ┌────▼────┐
                   │ PLANNER │           │ VALIDATOR│  │  RAG    │
                   │ + Qdrant│           │  (Audit) │  │  Memory │
                   └────┬────┘           └─────┬────┘  └─────────┘
                        │                      │
                        └──────────────────────┘
                                           │
                                    ┌──────▼──────┐
                                    │ PostgreSQL  │
                                    │  MongoDB    │
                                    └─────────────┘
```

---

## Slide 4 — Innovations Clés

### 1. Routage Sémantique Intelligent

Classification automatique des flux entrants :
- **Critical** → Alerte immédiate
- **Standard** → File asynchrone
- **Complex** → Enrichissement + RAG

### 2. Mémoire Contextuelle (RAG)

> *"La dernière extraction SAP a pris 45 minutes, et non 15"*

Base vectorielle Qdrant + embeddings historiques pour des estimations réalistes.

### 3. Multi-Agents Spécialisés

- **Extracteur** : Nettoyage + PII masking
- **Planificateur** : Optimisation sous contraintes
- **Validateur** : Audit + boucle de correction

---

## Slide 5 — Résilience Enterprise

### Graceful Degradation

| Scénario | Mécanisme | SLA |
|----------|-----------|-----|
| OpenAI 429 | Bascule Anthropic en < 2s | 99.9% |
| Timeout API | Circuit breaker + queue | 99.9% |
| Redis down | Stockage local JSON | 99.9% |
| PII détecté | Masquage automatique | 100% |

### Circuit Breaker

```
CLOSED (5 erreurs) → OPEN (60s) → HALF_OPEN → CLOSED
```

---

## Slide 6 — Stack & Performance

| Couche | Technologie | Performance |
|--------|-------------|-------------|
| Orchestration | n8n + Python | 1000+ tâches/h |
| LLM | GPT-4o + Claude 3.5 | Latence < 5s |
| Vector DB | Qdrant | Recherche < 50ms |
| SQL | PostgreSQL 15 | Durabilité ACID |
| Logs | MongoDB | Append-only, TTL 1an |

### SLAs

- **Disponibilité** : 99.9%
- **Latence extraction** : < 500ms
- **Latence planification** : < 5s
- **Taux d'erreur** : < 0.1%

---

## Slide 7 — Sécurité & Gouvernance

### Sanitization PII

| Type | Masque |
|------|--------|
| Email | `[EMAIL]` |
| Téléphone | `[PHONE]` |
| Date | `[DATE]` |

### Gestion des Secrets

- **Développement** : Variables d'environnement
- **Production** : AWS Secrets Manager / Vault
- **Rotation** : 90 jours
- **CI/CD** : TruffleHog scan

### Conformité

✅ RGPD — ✅ ISO 27001 — ✅ SOC 2

---

## Slide 8 — Livrables

| # | Livrable | Statut |
|---|----------|--------|
| 1 | Architecture Documentée (C4, Mermaid) | ✅ |
| 2 | Data Flow Diagram (Niveau 0, 1, 2) | ✅ |
| 3 | Docker Compose (Stack complète) | ✅ |
| 4 | Dépôt Git (46 fichiers, 3600+ lignes) | ✅ |
| 5 | Tests de Résilience (6 scénarios) | ✅ |
| 6 | CI/CD (GitHub Actions + GitLab CI) | ✅ |
| 7 | API Reference (FastAPI, OpenAPI) | ✅ |
| 8 | Modèle de Sécurité | ✅ |

---

## Slide 9 — Démonstration

### Commandes de déploiement

```bash
# 1. Configuration
cp .env.example .env

# 2. Lancement stack
docker-compose up -d

# 3. Vérification
curl http://localhost:5678   # n8n
curl http://localhost:6333   # Qdrant
curl http://localhost:8000   # Agents
```

### Services démarrés

- **n8n** (port 5678) — Orchestration visuelle
- **Qdrant** (port 6333) — Mémoire vectorielle
- **PostgreSQL** (port 5432) — Données structurées
- **MongoDB** (port 27017) — Logs d'audit
- **RabbitMQ** (port 15672) — Event bus

---

## Slide 10 — Roadmap & Prochaines Étapes

| Phase | Livrable | Échéance |
|-------|----------|----------|
| **Phase 1** | Déploiement K8s + Helm | Juillet 2026 |
| **Phase 2** | Prometheus + Grafana | Juillet 2026 |
| **Phase 3** | Chaos Engineering | Août 2026 |
| **Phase 4** | Auto-scaling Qdrant | Août 2026 |
| **Phase 5** | ADR-004 Kafka vs RabbitMQ | Septembre 2026 |

---

## Slide 11 — Questions & Discussion

### Points à discuter

1. **Budget** : Validation des coûts API (OpenAI, Anthropic)
2. **Infrastructure** : On-premise vs Cloud managé
3. **Équipe** : Besoin en DevOps / Data Engineer
4. **Intégrations** : ERP existant, CRM, Google Workspace

---

## Merci

**Contact** : youssef.amarzou@yahoo.com — Youssef AMARZOU
**Repository** : `github.com/Youssef-AMARZOU/project-omni`

*Built with intelligence. Powered by agents. Orchestrated by OMNI.*

---

**Annexe — Métriques de Performance**

| Test | Résultat | Objectif |
|------|----------|----------|
| Fallback LLM | 1.2s | < 2s ✅ |
| Validation | 45ms | < 2s ✅ |
| Détection PII | 100% | 100% ✅ |
| Circuit Breaker | < 1ms | < 1ms ✅ |
| Uptime simulé | 99.95% | 99.9% ✅ |
