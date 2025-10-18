# backend/app/agents/storage_agent.py

from typing import Dict
from .. import schemas

class StorageAgent:
    def __init__(self):
        # Basit in-memory veritabanı
        self.results_db: Dict[str, schemas.GradingResult] = {}

    def save_result(self, result: schemas.GradingResult):
        key = f"{result.job_id}_{result.student_id}_{result.question_id}"
        self.results_db[key] = result
        print(f"Result for {key} saved.")

    def get_result(self, job_id: str, student_id: str, question_id: str) -> schemas.GradingResult | None:
        key = f"{job_id}_{student_id}_{question_id}"
        return self.results_db.get(key)