# API Reference — Project OMNI Internal Agents

## Base URL

```
http://omni-agents:8000
```

## Endpoints

### GET /health

Health check du service.

**Response** :
```json
{
  "status": "healthy",
  "service": "omni-agents",
  "version": "2.0.0"
}
```

---

### POST /extract

Déclenche l'Agent Extracteur.

**Request** :
```json
{
  "id": "task-001",
  "source": "webhook",
  "email": "user@example.com",
  "description": "Extraction de données"
}
```

**Response** :
```json
{
  "task_id": "task-001",
  "source": "webhook",
  "priority": "standard",
  "raw_input": {...},
  "cleaned_data": {"email": "[EMAIL]", "description": "Extraction de données"},
  "schema_version": "1.0.0",
  "pii_masked": true,
  "confidence": 0.95
}
```

---

### POST /plan

Déclenche l'Agent Planificateur.

**Request** :
```json
{
  "task_id": "task-001",
  "cleaned_data": {"description": "Extraction de données"}
}
```

**Response** :
```json
{
  "task_id": "task-001",
  "estimated_duration_minutes": 45,
  "assigned_resources": ["data-team"],
  "constraints": [],
  "schedule": [],
  "dependencies": [],
  "confidence": 0.9,
  "rag_context_used": true
}
```

---

### POST /validate

Déclenche l'Agent Validateur.

**Request** :
```json
{
  "task_id": "task-001",
  "estimated_duration_minutes": 45,
  "assigned_resources": ["data-team"],
  "schedule": []
}
```

**Response** :
```json
{
  "task_id": "task-001",
  "is_valid": true,
  "violations": [],
  "corrected_plan": null,
  "audit_score": 1.0,
  "confidence": 0.95
}
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| E100 | 400 | Extraction failed |
| E200 | 502 | LLM timeout |
| E300 | 422 | Validation failed |
| E400 | 503 | Database unavailable |
| E500 | 500 | Internal error |

## Authentication

Les appels internes utilisent un JWT signé avec la clé partagée `OMNI_INTERNAL_JWT_SECRET`.

## Rate Limiting

- 100 req/min par IP
- 1000 req/min par service

## OpenAPI

La documentation interactive est disponible à `/docs` (Swagger UI) et `/openapi.json`.
