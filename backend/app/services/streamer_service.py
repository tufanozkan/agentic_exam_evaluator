# backend/app/services/streamer_service.py
import asyncio

class Job:
    """Bir değerlendirme işini temsil eder."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status: str = "starting"