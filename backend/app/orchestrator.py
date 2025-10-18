# backend/app/orchestrator.py

import asyncio
import uuid
from pathlib import Path
from typing import Dict, List
import aiofiles
import traceback

from fastapi import UploadFile

from . import schemas
from .agents.pdf_parser_agent import PDFParserAgent
from .agents.grader_agent import GraderAgent
from .agents.verifier_agent import VerifierAgent
from .agents.feedback_agent import FeedbackAgent
from .agents.summary_agent import SummaryAgent
from .agents.storage_agent import StorageAgent
from .services.streamer_service import Job
from .services.connection_manager import manager  # ConnectionManager'ı import et

class OrchestratorAgent:
    # ... (__init__, create_job, save_uploaded_files metodları aynı) ...
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.upload_dir = Path("temp_uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
        # Her ajandan birer nesne oluşturuyoruz. Artık tüm yetenekler burada.
        self.parser_agent = PDFParserAgent()
        self.grader_agent = GraderAgent()
        self.verifier_agent = VerifierAgent()
        self.feedback_agent = FeedbackAgent()
        self.summary_agent = SummaryAgent()
        self.storage_agent = StorageAgent()

    def create_job(self) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(job_id)
        self.jobs[job_id] = job
        return job

    async def save_uploaded_files(self, job_id: str, answer_key: UploadFile, student_sheets: List[UploadFile]) -> Dict:
        job_dir = self.upload_dir / job_id
        job_dir.mkdir(exist_ok=True)
        
        paths = {"answer_key": job_dir / answer_key.filename}
        async with aiofiles.open(paths["answer_key"], 'wb') as f:
            await f.write(await answer_key.read())
            
        paths["student_sheets"] = []
        for student_file in student_sheets:
            student_path = job_dir / student_file.filename
            async with aiofiles.open(student_path, 'wb') as f:
                await f.write(await student_file.read())
            paths["student_sheets"].append(student_path)
        return paths

    # --- TAMAMEN GÜNCELLENMİŞ process_job METODU ---
    async def process_job(self, job_id: str, file_paths: Dict):
        job = self.jobs.get(job_id)
        if not job: return
        
        job.status = "processing"
        
        try:
            with open(file_paths["answer_key"], "rb") as f:
                key_content = f.read()
            question_objects = await asyncio.to_thread(self.parser_agent.parse_answer_key, key_content)

            total_questions = len(question_objects)
            initial_event = schemas.StreamEvent(
                event="job_started",
                data={"total_questions": total_questions}
            )
            await manager.send_event_to_job(initial_event.model_dump_json(), job_id)
            
            for student_path in file_paths["student_sheets"]:
                student_id = student_path.stem
                
                with open(student_path, "rb") as f:
                    student_content = f.read()
                student_answers = await asyncio.to_thread(self.parser_agent.parse_student_answers, student_content, student_id)
                
                all_results_for_student = []
                
                for question in question_objects:
                    student_answer = next((ans for ans in student_answers if ans.question_id == question.question_id), None)
                    if not student_answer: continue

                    raw_result = await asyncio.to_thread(self.grader_agent.grade_question, question, student_answer, job_id)
                    verified_result = await asyncio.to_thread(self.verifier_agent.verify_grading_result, raw_result)
                    
                    feedback_text = await asyncio.to_thread(
                        self.feedback_agent.generate_feedback_for_question,
                        verified_result,
                        student_answer.student_answer_text,
                        question.question_text
                    )
                    
                    result_data = verified_result.model_dump(mode="json")
                    result_data['friendly_feedback'] = feedback_text
                    
                    event = schemas.StreamEvent(event="partial_result", data=result_data)
                    # DÜZELTME: Kuyruk yerine manager kullan
                    await manager.send_event_to_job(event.model_dump_json(), job_id)
                    
                    all_results_for_student.append(verified_result)
                    await asyncio.to_thread(self.storage_agent.save_result, verified_result)

                if all_results_for_student:
                    summary_text = await asyncio.to_thread(self.summary_agent.generate_summary_report, all_results_for_student)
                    student_done_event = schemas.StreamEvent(
                        event="student_summary",
                        data={"student_id": student_id, "summary_report": summary_text}
                    )
                    # DÜZELTME: Kuyruk yerine manager kullan
                    await manager.send_event_to_job(student_done_event.model_dump_json(), job_id)

            job.status = "completed"
            job_done_event = schemas.StreamEvent(event="job_done", data={"job_id": job_id})
            # DÜZELTME: Kuyruk yerine manager kullan
            await manager.send_event_to_job(job_done_event.model_dump_json(), job_id)
        
        except Exception as e:
            job.status = "failed"
            print(f"Job {job_id} failed with error: {e}")
            traceback.print_exc()
            error_event = schemas.StreamEvent(event="error", data={"message": str(e)})
            # DÜZELTME: Kuyruk yerine manager kullan (Hata durumunda da)
            await manager.send_event_to_job(error_event.model_dump_json(), job_id)
        
        # 'finally' bloğuna artık gerek yok çünkü disconnect işlemini main.py'deki
        # websocket_endpoint'in kendisi yapıyor.