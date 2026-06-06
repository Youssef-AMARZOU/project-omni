import json
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator
from src.utils.logger import get_logger
from src.utils.fallback import LLMClient

logger = get_logger("omni.validator")

class ValidationResult(BaseModel):
    task_id: str
    is_valid: bool
    violations: List[str]
    corrected_plan: Optional[Dict[str, Any]] = None
    audit_score: float = 1.0
    confidence: float = 0.95

    @field_validator("audit_score")
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

class ValidatorAgent:
    LLM_TIMEOUT = 15.0

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.logger = logger

    async def validate(self, plan: Dict[str, Any], original_payload: Dict[str, Any]) -> ValidationResult:
        task_id = plan.get("task_id", "unknown")
        self.logger.info("validator_start", task_id=task_id)
        violations = self._check_hard_rules(plan)
        if not violations:
            llm_violations = await self._llm_audit(plan, original_payload)
            violations.extend(llm_violations)
        is_valid = len(violations) == 0
        corrected_plan = None
        if not is_valid:
            corrected_plan = await self._request_correction(plan, violations)
        raw_score = 1.0 - (len(violations) * 0.1)
        result = ValidationResult(
            task_id=task_id,
            is_valid=is_valid,
            violations=violations,
            corrected_plan=corrected_plan,
            audit_score=max(0.0, raw_score),
            confidence=0.95 if is_valid else 0.7,
        )
        self.logger.info("validator_complete", task_id=task_id, is_valid=is_valid, violations_count=len(violations))
        return result

    def _check_hard_rules(self, plan: Dict[str, Any]) -> List[str]:
        violations = []
        duration = plan.get("estimated_duration_minutes", 0)
        if duration <= 0:
            violations.append("Duree estimee invalide (<= 0).")
        if duration > 480:
            violations.append("Duree estimee > 8h - necessite decoupage en sous-taches.")
        resources = plan.get("assigned_resources", [])
        if not resources:
            violations.append("Aucune ressource assignee.")
        schedule = plan.get("schedule", [])
        for i in range(len(schedule)):
            for j in range(i + 1, len(schedule)):
                s1, s2 = schedule[i], schedule[j]
                if s1.get("resource") == s2.get("resource"):
                    start1, end1 = s1.get("start", ""), s1.get("end", "")
                    start2, end2 = s2.get("start", ""), s2.get("end", "")
                    if start1 and end1 and start2 and end2 and start1 < end2 and start2 < end1:
                        violations.append(f"Chevauchement detecte pour la ressource {s1.get('resource')}.")
                        break
            else:
                continue
            break
        return violations

    async def _llm_audit(self, plan: Dict[str, Any], original_payload: Dict[str, Any]) -> List[str]:
        prompt = (
            "Tu es un auditeur qualite. Analyse le plan suivant et liste les violations "
            "metier ou incoherences sous forme de liste JSON de strings. "
            "Si tout est correct, renvoie [].\n\n"
            f"PLAN : {json.dumps(plan, ensure_ascii=False, default=str)}\n"
            f"CONTEXTE ORIGINAL : {json.dumps(original_payload, ensure_ascii=False, default=str)}\n"
        )
        try:
            response = await asyncio.wait_for(
                self.llm.chat(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=500,
                ),
                timeout=self.LLM_TIMEOUT,
            )
            violations = json.loads(response)
            if not isinstance(violations, list):
                return []
            return [v for v in violations if isinstance(v, str)]
        except asyncio.TimeoutError:
            self.logger.warning("llm_audit_timeout")
            return []
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.warning("llm_audit_parse_failed", error=str(e))
            return []
        except Exception as e:
            self.logger.warning("llm_audit_failed", error=str(e))
            return []

    async def _request_correction(self, plan: Dict[str, Any], violations: List[str]) -> Dict[str, Any]:
        prompt = (
            "Corrige le plan suivant en tenant compte des violations detectees. "
            "Renvoie UNIQUEMENT le plan corrige au format JSON.\n\n"
            f"VIOLATIONS : {json.dumps(violations, ensure_ascii=False)}\n"
            f"PLAN : {json.dumps(plan, ensure_ascii=False, default=str)}"
        )
        try:
            response = await asyncio.wait_for(
                self.llm.chat(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1500,
                ),
                timeout=self.LLM_TIMEOUT,
            )
            corrected = json.loads(response)
            if isinstance(corrected, dict):
                return corrected
            self.logger.warning("correction_invalid_format")
            return plan
        except (json.JSONDecodeError, TypeError):
            self.logger.warning("correction_parse_failed")
            return plan
        except asyncio.TimeoutError:
            self.logger.warning("correction_timeout")
            return plan
        except Exception as e:
            self.logger.error("correction_failed", error=str(e))
            return plan