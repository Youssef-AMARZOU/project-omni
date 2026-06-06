# Architecture Système — Project OMNI Enterprise

## 1. Vue d'ensemble

Project OMNI est une architecture **Event-Driven Micro-Agents** conçue pour l'orchestration de pipelines ETL d'entreprise avec capacités cognitives.

---

## 2. Diagramme de Composants (C4 - Level 2)

```mermaid
graph TB
    subgraph Ingestion["Couche Ingestion"]
        WH[Webhook]
        CDC[Change Data Capture]
        RK[RabbitMQ / Kafka]
    end

    subgraph Orchestration["Couche Orchestration"]
        N8N[n8n Workflow Engine]
        ET[Error Trigger]
        FB[Fallback Node]
    end

    subgraph Cognitive["Couche Cognitive"]
        LLM1[OpenAI GPT-4o]
        LLM2[Anthropic Claude 3.5]
        LLM3[Local Model]
    end

    subgraph Agents["Couche Multi-Agents"]
        EXT[Agent Extracteur]
        PLN[Agent Planificateur]
        VAL[Agent Validateur]
    end

    subgraph Memory["Couche Mémoire"]
        QDR[Qdrant Vector DB]
        EMB[Embedding Model]
    end

    subgraph Persistence["Couche Persistance"]
        PG[(PostgreSQL)]
        MG[(MongoDB Logs)]
        RD[(Redis Queue)]
    end

    WH --> N8N
    CDC --> N8N
    RK --> N8N
    N8N --> EXT
    EXT --> PLN
    PLN --> QDR
    QDR --> PLN
    PLN --> VAL
    VAL -->|Approved| PG
    VAL -->|Correction| PLN
    N8N --> LLM1
    LLM1 -->|429/500| FB
    FB --> LLM2
    FB --> MG
    EXT --> MG
    PLN --> MG
    VAL --> MG
    N8N --> RD
    EXT --> RD
    EMB --> QDR
```

---

## 3. Flux de Données (Séquence)

```mermaid
sequenceDiagram
    participant Source as Source (Webhook/CDC)
    participant N8N as Orchestrator n8n
    participant EXT as Extractor Agent
    participant QDR as Qdrant RAG
    participant PLN as Planner Agent
    participant VAL as Validator Agent
    participant PG as PostgreSQL
    participant MG as MongoDB

    Source->>N8N: Donnée brute
    N8N->>EXT: POST /extract
    EXT->>EXT: Sanitization PII
    EXT->>EXT: Classification LLM
    EXT->>MG: Log extraction
    EXT->>N8N: Payload structuré
    N8N->>PLN: POST /plan
    PLN->>QDR: Search similar tasks
    QDR->>PLN: Historical context
    PLN->>PLN: Optimize schedule
    PLN->>MG: Log planning
    PLN->>N8N: TaskPlan JSON
    N8N->>VAL: POST /validate
    VAL->>VAL: Hard rules check
    VAL->>VAL: LLM audit
    VAL->>MG: Log validation
    alt Valid
        VAL->>PG: INSERT approved plan
    else Invalid
        VAL->>N8N: Correction required
        N8N->>PLN: Re-plan with feedback
    end
```

---

## 4. Patterns Utilisés

| Pattern | Implémentation | Fichier |
|---------|---------------|---------|
| Circuit Breaker | `CircuitBreaker` class | `src/utils/circuit_breaker.py` |
| Fallback | `LLMClient` with catch | `src/utils/fallback.py` |
| Event Bus | Redis Pub/Sub | `src/utils/message_bus.py` |
| State Machine | JSON persistence | `src/utils/state_manager.py` |
| RAG | Qdrant + OpenAI embeddings | `src/rag/` |
| Graceful Degradation | n8n Error Trigger → Anthropic | `n8n-workflows/error-handling.json` |

---

## 5. Décisions d'Architecture (ADR)

### ADR-001 : Event-Driven vs CRON
**Décision** : Architecture event-driven (RabbitMQ + Webhooks) plutôt que CRON.
**Motivation** : Réactivité immédiate, scalabilité horizontale, traçabilité.

### ADR-002 : Qdrant vs Pinecone
**Décision** : Qdrant auto-hébergé en Docker.
**Motivation** : Souveraineté des données, coût nul, intégration on-premise.

### ADR-003 : n8n vs Airflow
**Décision** : n8n pour l'orchestration visuelle, Python natif pour la logique complexe.
**Motivation** : Rapidité de prototypage + puissance algorithmique.

---

## 6. Matrice de Dépendances

| Composant | Dépend de | Utilisé par |
|-----------|-----------|-------------|
| n8n | PostgreSQL, Redis | Webhooks, Agents |
| Agent Extracteur | LLM (Haiku), MongoDB | n8n |
| Agent Planificateur | GPT-4o, Qdrant | n8n |
| Agent Validateur | GPT-4o | n8n |
| Qdrant | - | Planner, RAG |
| PostgreSQL | - | n8n, ETL Output |
| MongoDB | - | Tous les agents |
| Redis | - | n8n, Message Bus |
