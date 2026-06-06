# Data Flow Diagram — Project OMNI Enterprise

## DFD Niveau 0 (Contexte)

```mermaid
graph LR
    A[Sources de Données<br/>ERP, Webhooks, CDC] -->|Données brutes| B[Project OMNI]
    B -->|Plans & Rapports| C[Destinations<br/>ERP, API, Bases SQL]
    D[Administrateurs] -->|Configuration| B
    B -->|Alertes| E[Monitoring & Logs]
```

## DFD Niveau 1 (Processus Principaux)

```mermaid
graph TB
    subgraph E["Entités Externes"]
        SRC[Sources]
        DST[Destinations]
        MON[Monitoring]
    end

    subgraph P["Processus"]
        P1[1.0 Ingestion]
        P2[2.0 Triage Sémantique]
        P3[3.0 Extraction & Nettoyage]
        P4[4.0 Planification RAG]
        P5[5.0 Validation]
        P6[6.0 Écriture]
        P7[7.0 Audit & Logs]
    end

    subgraph D["Données"]
        D1[(Raw Queue)]
        D2[(Structured Queue)]
        D3[(Vector DB)]
        D4[(PostgreSQL)]
        D5[(MongoDB)]
    end

    SRC -->|raw_payload| P1
    P1 -->|raw_event| D1
    D1 --> P2
    P2 -->|classified_event| D2
    D2 --> P3
    P3 -->|cleaned_data| D2
    P2 -->|critical_alert| MON
    D3 --> P4
    P4 -->|plan| D2
    D2 --> P5
    P5 -->|approved_plan| P6
    P5 -->|correction| P4
    P6 -->|final_record| D4
    P3 -->|audit_log| D5
    P4 -->|audit_log| D5
    P5 -->|audit_log| D5
    P6 -->|audit_log| D5
    P5 -->|anomaly_alert| MON
```

## DFD Niveau 2 — Processus 4.0 (Planification RAG)

```mermaid
graph LR
    P4[4.0 Planification] --> P4A[4.1 Embedding Query]
    P4A --> QDR[(Qdrant)]
    QDR --> P4B[4.2 Search Similar]
    P4B --> P4C[4.3 Context Assembly]
    P4C --> P4D[4.4 LLM Optimization]
    P4D --> P4E[4.5 Constraint Check]
    P4E --> P4F[4.6 Plan Output]
    P4F --> D2[(Structured Queue)]
```

---

## Table des Flux de Données

| Flux | Source | Destination | Type | Format | Fréquence |
|------|--------|-------------|------|--------|-----------|
| raw_payload | Webhook | Ingestion | Push | JSON | Variable |
| classified_event | Triage | Extraction | Queue | JSON | Temps réel |
| cleaned_data | Extraction | Planification | Queue | JSON | Temps réel |
| historical_context | Qdrant | Planification | Pull | Vector | À la demande |
| plan | Planification | Validation | Queue | JSON | Temps réel |
| correction | Validation | Planification | Feedback | JSON | Si invalide |
| approved_plan | Validation | PostgreSQL | Write | SQL | Temps réel |
| audit_log | Tous | MongoDB | Write | BSON | Continu |
| critical_alert | Triage | Monitoring | Push | JSON | Immédiat |
