# backend/app/agents/storage_agent.py

from typing import Dict, List, Any
from .. import schemas

class StorageAgent:
    def __init__(self):
        self.results_db: Dict[str, schemas.GradingResult] = {}
        self.chat_histories: Dict[str, List[Dict[str, Any]]] = {}

    def _get_key(self, job_id: str, student_id: str, question_id: str) -> str:
        """Tüm metodlarda kullanılacak standart bir anahtar oluşturur."""
        return f"{job_id}_{student_id}_{question_id}"

    def save_result(self, result: schemas.GradingResult):
        #anahtar için _get_key
        key = self._get_key(result.job_id, result.student_id, result.question_id)
        self.results_db[key] = result
        print(f"Result for {key} saved.")

    def get_result(self, job_id: str, student_id: str, question_id: str) -> schemas.GradingResult | None:
        #anahtar için _get_key
        key = self._get_key(job_id, student_id, question_id)
        return self.results_db.get(key)
        
    def get_chat_history(self, job_id: str, student_id: str, question_id: str) -> List[Dict[str, Any]]:
        #anahtar için _get_key
        key = self._get_key(job_id, student_id, question_id)
        return self.chat_histories.get(key, [])

    def save_chat_history(self, job_id: str, student_id: str, question_id: str, history: List[Dict[str, Any]]):
        #anahtar için _get_key
        key = self._get_key(job_id, student_id, question_id)
        self.chat_histories[key] = history