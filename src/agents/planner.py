import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from src.utils.logger import get_logger
from src.utils.fallback import LLMClient
from src.rag.vector_store import VectorStore

logger = get_logger("omni.planner")

class TaskPlan(BaseModel):
    """Plan de tâche optimisé généré par l'Agent Planificateur."""
    task_id: str
    estimated_duration_minutes: int
    assigned_resources: List[str]
    constraints: List[str]
    schedule: List[Dict[str, Any]]
    dependencies: List[str]
    confidence: float
    rag_context_used: bool = False

class PlannerAgent:
    """
    Agent Planificateur — Optimise l'allocation des ressources
    sous contraintes métier en s'appuyant sur la mémoire RAG.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.llm = llm_client or LLMClient()
        self.vs = vector_store or VectorStore()
        self.logger = logger

    async def plan(self, extracted_payload: Dict[str, Any]) -> TaskPlan:
        self.logger.info("planner_start", task_id=extracted_payload["task_id"])

        # 1. Recherche RAG : historique de tâches similaires
        rag_results = await self.vs.search_similar(
            query=json.dumps(extracted_payload["cleaned_data"]),
            top_k=3,
        )
        historical_context = self._format_rag(rag_results)

        # 2. Construction du prompt d'optimisation
        prompt = self._build_prompt(extracted_payload, historical_context)

        # 3. Appel LLM principal (GPT-4o) avec fallback
        try:
            response = await self.llm.chat(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            plan_data = json.loads(response)
        except Exception as e:
            self.logger.error("planning_failed", error=str(e))
            raise

        # 4. Validation basique du plan
        plan = TaskPlan(
            task_id=extracted_payload["task_id"],
            estimated_duration_minutes=plan_data.get("estimated_duration_minutes", 30),
            assigned_resources=plan_data.get("assigned_resources", []),
            constraints=plan_data.get("constraints", []),
            schedule=plan_data.get("schedule", []),
            dependencies=plan_data.get("dependencies", []),
            confidence=plan_data.get("confidence", 0.8),
            rag_context_used=len(rag_results) > 0,
        )

        self.logger.info("planner_complete", task_id=plan.task_id, duration=plan.estimated_duration_minutes)
        return plan

    def _system_prompt(self) -> str:
        return (
            "Tu es un agent planificateur d'entreprise spécialisé en optimisation "
            "sous contraintes. Tu produis des plans au format JSON strict avec les champs : "
            "estimated_duration_minutes (int), assigned_resources (list[str]), "
            "constraints (list[str]), schedule (list d'étapes), dependencies (list[str]), "
            "confidence (float 0-1). Tu dois tenir compte du contexte historique fourni."
        )

    def _build_prompt(self, payload: Dict[str, Any], historical_context: str) -> str:
        return (
            f"TÂCHE À PLANIFIER :\n{json.dumps(payload['cleaned_data'], ensure_ascii=False, indent=2)}\n\n"
            f"CONTEXTE HISTORIQUE (RAG) :\n{historical_context}\n\n"
            "Génère un plan JSON optimisé."
        )

    def _format_rag(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "Aucun historique similaire trouvé."
        lines = []
        for r in results:
            lines.append(f"- Tâche similaire (score {r['score']:.2f}) : {r['payload']}")
        return "\n".join(lines)
