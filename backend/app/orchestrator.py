import asyncio
import uuid
from pathlib import Path
from typing import Dict, List
import aiofiles

from fastapi import UploadFile

from . import schemas
from .parser import parse_answer_key, parse_student_answers
from .evaluator import GraderAgent
from .verifier import VerifierAgent
from .reporting import ReportingAgent

class Job:
    """Bir değerlendirme işini ve onun iletişim kuyruğunu temsil eden sınıf."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status: str = "starting"
        self.results_queue = asyncio.Queue()

class OrchestratorAgent:
    """
    Tüm değerlendirme iş akışını yöneten, ajanları sırayla çalıştıran ve
    sonuçları canlı yayın için bir kuyruğa koyan ana yönetici ajan.
    """
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.grader = GraderAgent()
        self.verifier = VerifierAgent()
        self.reporter = ReportingAgent()
        self.upload_dir = Path("temp_uploads")
        self.upload_dir.mkdir(exist_ok=True)

    def create_job(self) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(job_id)
        self.jobs[job_id] = job
        return job

    async def save_uploaded_files(self, job_id: str, answer_key: UploadFile, student_sheets: List[UploadFile]) -> Dict:
        job_dir = self.upload_dir / job_id
        job_dir.mkdir()
        
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

    async def process_job(self, job_id: str, file_paths: Dict):
        """
        Bir işin tüm adımlarını (Parse, Grade, Verify, Report) asenkron olarak çalıştırır.
        (Artık engelleyici çağrılar için asyncio.to_thread kullanıyor)
        """
        job = self.jobs[job_id]
        job.status = "processing"
        
        try:
            # --- Engelleyici Dosya Okuma İşlemleri ---
            # Bunları ayrı bir thread'de çalıştırarak ana döngüyü kilitlemiyoruz.
            with open(file_paths["answer_key"], "rb") as f:
                key_content = f.read()
            question_objects = await asyncio.to_thread(parse_answer_key, key_content)
            
            for student_path in file_paths["student_sheets"]:
                student_id = student_path.stem
                
                with open(student_path, "rb") as f:
                    student_content = f.read()
                student_answers = await asyncio.to_thread(parse_student_answers, student_content, student_id)
                
                all_results_for_student = []
                
                for question in question_objects:
                    student_answer = next((ans for ans in student_answers if ans.question_id == question.question_id), None)
                    if not student_answer: continue

                    # --- Engelleyici Ajan Çağrıları ---
                    # Her bir ajan çağrısını ayrı bir thread'de çalıştırıyoruz.
                    raw_result = await asyncio.to_thread(self.grader.grade_question, question, student_answer, job_id)
                    verified_result = await asyncio.to_thread(self.verifier.verify_grading_result, raw_result)
                    
                    event = schemas.StreamEvent(
                        event="partial_result",
                        data=verified_result.model_dump(mode="json")
                    )
                    await job.results_queue.put(event)
                    all_results_for_student.append(verified_result)

                if all_results_for_student:
                    # Raporlama da bir LLM çağrısı olduğu için engelleyicidir.
                    summary_text = await asyncio.to_thread(self.reporter.generate_summary_report, all_results_for_student)
                    student_done_event = schemas.StreamEvent(
                        event="student_summary",
                        data={"student_id": student_id, "summary_report": summary_text}
                    )
                    await job.results_queue.put(student_done_event)

            job.status = "completed"
            await job.results_queue.put(schemas.StreamEvent(event="job_done", data={"job_id": job_id}))
        
        except Exception as e:
            job.status = "failed"
            # Hatanın izini sürmek için daha detaylı loglama
            import traceback
            print(f"Job {job_id} failed with error: {e}")
            traceback.print_exc()
            error_event = schemas.StreamEvent(event="error", data={"message": str(e)})
            await job.results_queue.put(error_event)
        
        finally:
            await job.results_queue.put(None)