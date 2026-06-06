import json
import os
from typing import Any, Dict
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.state_manager")

class StateManager:
    """
    Gestionnaire d'état persistant.
    Stocke l'état de chaque tâche dans un fichier JSON local
    (remplaçable par PostgreSQL en production).
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or settings.omni_data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _path(self, task_id: str) -> str:
        return os.path.join(self.data_dir, f"{task_id}.json")

    def update(self, task_id: str, key: str, value: Any):
        state = self._load(task_id)
        state[key] = value
        self._save(task_id, state)
        logger.debug("state_updated", task_id=task_id, key=key)

    def get(self, task_id: str, key: str, default: Any = None) -> Any:
        state = self._load(task_id)
        return state.get(key, default)

    def _load(self, task_id: str) -> Dict[str, Any]:
        path = self._path(task_id)
        if not os.path.exists(path):
            return {"task_id": task_id}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, task_id: str, state: Dict[str, Any]):
        path = self._path(task_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
