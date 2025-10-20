# backend/app/services/streamer_service.py
import asyncio

class Job:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status: str = "starting"