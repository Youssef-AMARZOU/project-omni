# Spécifications Techniques — Project OMNI Enterprise

## 1. Stack Technologique

| Couche | Technologie | Version | Justification |
|--------|-------------|---------|---------------|
| Orchestration | n8n | latest | Workflow visuel, rapidité |
| LLM Principal | OpenAI GPT-4o | v1 | Raisonnement complexe |
| LLM Secondaire | Anthropic Claude 3.5 | v1 | Fallback rapide |
| LLM Local | sentence-transformers | 2.x | Embedding offline |
| Vector DB | Qdrant | 1.7+ | On-premise, open source |
| SQL | PostgreSQL | 15 | Données structurées |
| NoSQL | MongoDB | 7 | Logs & audit |
| Queue | Redis | 7 | Pub/Sub & cache |
| Event Bus | RabbitMQ | 3 | Messages inter-services |
| Langage | Python | 3.11 | Pandas, FastAPI, async |
| API | FastAPI | 0.110+ | OpenAPI, async |
| Container | Docker | 24+ | Isolation, portabilité |
| CI/CD | GitHub Actions | - | Automatisation |

## 2. Spécifications des Composants

### 2.1 Orchestrateur n8n

- **Ports** : 5678 (HTTP)
- **Authentification** : Basic Auth
- **Persistance** : PostgreSQL (pas de SQLite en production)
- **Queue** : Redis Bull
- **Backups** : Workflows exportés en JSON dans `n8n-workflows/`

### 2.2 Agent Extracteur

- **Input** : JSON arbitraire (max 1MB)
- **Output** : `ExtractedPayload` (Pydantic)
- **PII** : Masquage en < 100ms
- **Classification** : 3 classes (critical, standard, complex)
- **Timeout** : 5s

### 2.3 Agent Planificateur

- **Input** : `ExtractedPayload`
- **Output** : `TaskPlan` (JSON structuré)
- **RAG** : Top-3 similar tasks
- **Optimisation** : Durée estimée ajustée historique
- **Timeout** : 30s

### 2.4 Agent Validateur

- **Input** : `TaskPlan` + `ExtractedPayload`
- **Output** : `ValidationResult`
- **Règles dures** : Durée > 0, ressources assignées, pas de chevauchement
- **Audit LLM** : Détection d'anomalies métier
- **Timeout** : 15s

### 2.5 Vector Store (Qdrant)

- **Dimension** : 3072 (text-embedding-3-large)
- **Distance** : Cosine
- **Index** : HNSW
- **TTL** : Aucun (archivage manuel)

## 3. SLAs & Performance

| Métrique | Objectif | Méthode de mesure |
|----------|----------|-------------------|
| Disponibilité | 99.9% | Uptime monitoring |
| Latence ingestion → extraction | < 500ms | Prometheus histogram |
| Latence planification | < 5s | Prometheus histogram |
| Latence validation | < 2s | Prometheus histogram |
| Taux d'erreur | < 0.1% | Counter errors / total |
| Fallback activation | < 1% | Counter fallback |

## 4. Schéma de Données

### 4.1 PostgreSQL — `omni_tasks`

```sql
CREATE TABLE omni_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(100),
    priority VARCHAR(20) CHECK (priority IN ('critical', 'standard', 'complex')),
    status VARCHAR(50) CHECK (status IN ('extracted', 'planned', 'validated', 'approved', 'correction_required', 'failed')),
    plan JSONB,
    raw_input JSONB,
    cleaned_data JSONB,
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_omni_tasks_status ON omni_tasks(status);
CREATE INDEX idx_omni_tasks_priority ON omni_tasks(priority);
```

### 4.2 MongoDB — `omni_audit_logs`

```json
{
  "_id": "ObjectId",
  "timestamp": "ISODate",
  "agent": "string",
  "task_id": "string",
  "raw_input": "object",
  "prompt": "string",
  "output": "object",
  "confidence": "double",
  "model_used": "string",
  "trace_id": "string"
}
```

## 5. Gestion des Erreurs

### 5.1 Codes d'erreur

| Code | Description | Action |
|------|-------------|--------|
| E100 | Extraction failed | Retry × 3, fallback manual |
| E200 | LLM timeout | Fallback to Anthropic |
| E201 | Rate limit OpenAI | Queue + exponential backoff |
| E300 | Validation failed | Return to planner |
| E400 | DB connection lost | Circuit breaker + alert |
| E500 | Unknown error | Log + alert + manual review |

### 5.2 Retry Policy

```python
# Exponential backoff
retry_delays = [1, 2, 4, 8, 16]  # seconds
max_retries = 5
```

## 6. Monitoring

- **Prometheus** : Métriques custom via `prometheus-client`.
- **Grafana** : Dashboards latency, errors, throughput.
- **Alertmanager** : PagerDuty / Slack pour les SLA breaches.

## 7. Backup & Recovery

| Donnée | Fréquence | Méthode | RTO |
|--------|-----------|---------|-----|
| PostgreSQL | 1h | pg_dump + S3 | 1h |
| MongoDB | 1h | mongodump + S3 | 1h |
| Qdrant | 24h | Snapshot API | 4h |
| n8n Workflows | On change | Git commit | 15min |
