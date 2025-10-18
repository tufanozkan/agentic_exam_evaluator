# backend/app/services/streamer_service.py
import asyncio

class Job:
    """Bir değerlendirme işini ve onun iletişim kuyruğunu temsil eden sınıf."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status: str = "starting"
        self.results_queue = asyncio.Queue()