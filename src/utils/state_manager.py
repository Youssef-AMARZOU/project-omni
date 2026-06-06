import json
import os
import re
from typing import Any, Dict
from src.utils.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger("omni.state_manager")

class StateManager:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or settings.omni_data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _path(self, task_id: str) -> str:
        safe_id = re.sub(r'[^\w\-.]', '_', task_id)
        return os.path.join(self.data_dir, f"{safe_id}.json")

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
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("state_load_failed", task_id=task_id, error=str(e))
            return {"task_id": task_id}

    def _save(self, task_id: str, state: Dict[str, Any]):
        path = self._path(task_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error("state_save_failed", task_id=task_id, error=str(e))