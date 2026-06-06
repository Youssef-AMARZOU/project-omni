import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError
from src.utils.logger import get_logger
from src.utils.fallback import LLMClient

logger = get_logger("omni.validator")

class ValidationResult(BaseModel):
    """Résultat de validation de l'Agent Validateur."""
    task_id: str
    is_valid: bool
    violations: List[str]
    corrected_plan: Optional[Dict[str, Any]]
    audit_score: float
    confidence: float

class ValidatorAgent:
    """
    Agent Validateur — Audite la sortie du planificateur.
    Détecte les anomalies (chevauchements, violations métier)
    et renvoie la tâche en correction si nécessaire.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.logger = logger

    async def validate(self, plan: Dict[str, Any], original_payload: Dict[str, Any]) -> ValidationResult:
        self.logger.info("validator_start", task_id=plan.get("task_id", "unknown"))

        # 1. Règles métier programmées (rapide)
        violations = self._check_hard_rules(plan)

        # 2. Validation LLM (GPT-4o) pour les règles complexes
        if not violations:
            llm_violations = await self._llm_audit(plan, original_payload)
            violations.extend(llm_violations)

        is_valid = len(violations) == 0

        # 3. Correction si invalide
        corrected_plan = None
        if not is_valid:
            corrected_plan = await self._request_correction(plan, violations)

        result = ValidationResult(
            task_id=plan["task_id"],
            is_valid=is_valid,
            violations=violations,
            corrected_plan=corrected_plan,
            audit_score=1.0 - (len(violations) * 0.1),
            confidence=0.95 if is_valid else 0.7,
        )

        self.logger.info(
            "validator_complete",
            task_id=result.task_id,
            is_valid=is_valid,
            violations_count=len(violations),
        )
        return result

    def _check_hard_rules(self, plan: Dict[str, Any]) -> List[str]:
        """Règles métier codées en dur (rapide, déterministe)."""
        violations = []
        duration = plan.get("estimated_duration_minutes", 0)
        if duration <= 0:
            violations.append("Durée estimée invalide (<= 0).")
        if duration > 480:
            violations.append("Durée estimée > 8h — nécessite découpage en sous-tâches.")

        resources = plan.get("assigned_resources", [])
        if not resources:
            violations.append("Aucune ressource assignée.")

        # Détection de chevauchement basique
        schedule = plan.get("schedule", [])
        seen = set()
        for step in schedule:
            key = (step.get("start"), step.get("end"), step.get("resource"))
            if key in seen:
                violations.append(f"Chevauchement détecté pour la ressource {key[2]}.")
            seen.add(key)

        return violations

    async def _llm_audit(self, plan: Dict[str, Any], original_payload: Dict[str, Any]) -> List[str]:
        """Audit avancé par LLM."""
        prompt = (
            "Tu es un auditeur qualité. Analyse le plan suivant et liste les violations "
            "métier ou incohérences sous forme de liste JSON de strings. "
            "Si tout est correct, renvoie [].\n\n"
            f"PLAN : {json.dumps(plan, ensure_ascii=False)}\n"
            f"CONTEXTE ORIGINAL : {json.dumps(original_payload, ensure_ascii=False)}\n"
        )
        try:
            response = await self.llm.chat(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500,
            )
            violations = json.loads(response)
            if not isinstance(violations, list):
                return []
            return [v for v in violations if isinstance(v, str)]
        except Exception as e:
            self.logger.warning("llm_audit_failed", error=str(e))
            return []

    async def _request_correction(self, plan: Dict[str, Any], violations: List[str]) -> Dict[str, Any]:
        """Demande une correction au planificateur via LLM."""
        prompt = (
            "Corrige le plan suivant en tenant compte des violations détectées. "
            "Renvoie UNIQUEMENT le plan corrigé au format JSON.\n\n"
            f"VIOLATIONS : {json.dumps(violations, ensure_ascii=False)}\n"
            f"PLAN : {json.dumps(plan, ensure_ascii=False)}"
        )
        try:
            response = await self.llm.chat(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
            )
            return json.loads(response)
        except Exception as e:
            self.logger.error("correction_failed", error=str(e))
            return plan
