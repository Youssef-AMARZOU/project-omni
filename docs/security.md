# Modèle de Sécurité & Audit — Project OMNI Enterprise

## 1. Politique de Sécurité

### 1.1 Classification des Données

| Niveau | Exemples | Traitement |
|--------|----------|------------|
| **Public** | Documentation, Rapports | Libre |
| **Interne** | Métadonnées de tâches | Accès authentifié |
| **Confidentiel** | Données métier, PII | Chiffrement + Sanitization |
| **Critique** | Clés API, Tokens | Vault externe (AWS Secrets Manager) |

### 1.2 Principes fondamentaux

1. **Zero Trust** : Chaque agent authentifie ses appels.
2. **Least Privilege** : Accès minimal requis pour chaque rôle.
3. **Defense in Depth** : Sanitization, chiffrement, audit en couches.

---

## 2. Sanitization des Données (PII)

### 2.1 Processus de l'Agent Extracteur

```python
# src/agents/extractor.py
PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
    (r"\b(?:\+33\s?|0)[1-9](?:\s?\d{2}){4}\b", "[PHONE]"),
    (r"\b\d{1,2}\s+\w+\s+\d{4}\b", "[DATE]"),
]
```

### 2.2 Règles

- **Avant** envoi à tout LLM externe : masquage automatique.
- **Logs** : jamais de PII en clair dans les logs structurés.
- **Bases de données** : chiffrement AES-256 pour les champs sensibles.

---

## 3. Gestion des Secrets

### 3.1 Environnement de Développement

```bash
# .env.example (template public)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 3.2 Environnement de Production

- **AWS Secrets Manager** ou **HashiCorp Vault**.
- Rotation automatique des clés API tous les 90 jours.
- Aucun secret dans le code source (vérifié par CI).

### 3.3 CI/CD Secrets Scanning

```yaml
# .github/workflows/ci.yml
- name: Detect secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: main
```

---

## 4. Traçabilité & Audit

### 4.1 Format de Log d'Audit

```json
{
  "timestamp": "2026-06-06T12:00:00Z",
  "agent": "planner",
  "task_id": "task-abc-123",
  "raw_input": {"...": "sanitized"},
  "prompt": "Planifie la tâche X...",
  "output": {"plan": "..."},
  "confidence": 0.94,
  "model_used": "gpt-4o",
  "trace_id": "uuid-trace"
}
```

### 4.2 Stockage

- **MongoDB** : Collection `omni_audit_logs` avec TTL de 1 an.
- **Immutabilité** : Logs en append-only, suppression interdite.
- **Index** : `task_id`, `agent`, `timestamp` pour requêtes rapides.

---

## 5. Authentification & Autorisation

### 5.1 n8n
- Basic Auth avec mot de passe fort.
- Webhooks sécurisés par signature HMAC.

### 5.2 Agents Python
- JWT interne pour les appels inter-services.
- Rate limiting par IP et par token.

### 5.3 Bases de données
- PostgreSQL : SSL obligatoire, rôles séparés (read/write/admin).
- MongoDB : Authentication SCRAM-SHA-256, réplication chiffrée.
- Redis : AUTH password, bind localhost.

---

## 6. Conformité

| Norme | Application | Statut |
|-------|-------------|--------|
| RGPD | Sanitization PII, droit à l'oubli | ✅ |
| ISO 27001 | Gestion des secrets, audit | ✅ |
| SOC 2 | Traçabilité, haute disponibilité | ✅ |

---

## 7. Plan de Réponse aux Incidents

1. **Détection** : Alertes Prometheus/Grafana sur toute anomalie.
2. **Containment** : Circuit breaker automatique.
3. **Investigation** : Requête MongoDB par `trace_id`.
4. **Recovery** : Rollback du plan via `corrected_plan`.
5. **Post-mortem** : Rapport dans `docs/security/incidents/`.
