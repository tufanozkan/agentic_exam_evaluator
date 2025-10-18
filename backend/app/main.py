# backend/app/main.py

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path

from . import schemas
from .orchestrator import OrchestratorAgent
from .services.streamer_service import Job # Job sınıfını yeni yerinden import ediyoruz

app = FastAPI(
    title="AI-Driven Exam Evaluator Agent",
    description="An agentic system for automated exam assessment with explainability.",
    version="1.0.0" # Refactoring bitti, 1.0.0'a geçebiliriz!
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tek bir Orchestrator nesnesi oluşturuyoruz
orchestrator = OrchestratorAgent()

@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "OK", "message": "Exam Evaluator Agent is running."}

@app.post("/api/jobs", status_code=202, response_model=schemas.JobStatus, tags=["Jobs"])
async def create_assessment_job(
    background_tasks: BackgroundTasks,
    answer_key: UploadFile = File(...),
    student_sheets: List[UploadFile] = File(...)
):
    job = orchestrator.create_job()
    try:
        file_paths = await orchestrator.save_uploaded_files(job.job_id, answer_key, student_sheets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File saving failed: {e}")
    background_tasks.add_task(orchestrator.process_job, job.job_id, file_paths)
    return schemas.JobStatus(job_id=job.job_id, status=job.status)

@app.post("/api/dev/start-sample-job", response_model=schemas.JobStatus, tags=["Development"])
async def start_sample_job(background_tasks: BackgroundTasks):
    job = orchestrator.create_job()
    
    # --- DÜZELTME: Dosya yolunu daha sağlam hale getirelim ---
    # main.py dosyasının konumunu alıp, oradan 2 seviye yukarı çıkarak
    # projenin kök dizinine ulaşıyoruz.
    project_root = Path(__file__).parent.parent.parent
    base_path = project_root / "test_files"
    # --- DÜZELTME SONU ---
    
    file_paths = {
        "answer_key": base_path / "answer_key.pdf",
        "student_sheets": [
            base_path / "student_1.pdf", base_path / "student_2.pdf",
            base_path / "student_3.pdf", base_path / "student_4.pdf",
        ]
    }
    
    if not all(p.exists() for p in [file_paths["answer_key"]] + file_paths["student_sheets"]):
        # Hata mesajını daha bilgilendirici hale getirelim
        raise HTTPException(status_code=404, 
            detail=f"Sample PDF files not found. Searched in: '{base_path.resolve()}'")

    background_tasks.add_task(orchestrator.process_job, job.job_id, file_paths)
    return schemas.JobStatus(job_id=job.job_id, status=job.status)

@app.get("/api/jobs/{job_id}/stream", tags=["Jobs"])
async def stream_job_results(job_id: str):
    clean_job_id = job_id.strip().replace('"', '')
    job = orchestrator.jobs.get(clean_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{clean_job_id}' not found")

    async def event_generator():
        while True:
            event = await job.results_queue.get()
            if event is None: break
            yield f"data: {event.model_dump_json()}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")