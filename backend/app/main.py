# backend/app/main.py

import json
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware # YENİ
from typing import List
from pathlib import Path # YENİ

from . import schemas
from .orchestrator import OrchestratorAgent

# --- Uygulama ve Ajanların Başlatılması ---
app = FastAPI(
    title="AI-Driven Exam Evaluator Agent",
    description="An agentic system for automated exam assessment with explainability.",
    version="0.2.1" # Sürümü güncelledik
)

# --- YENİ: CORS (Cross-Origin Resource Sharing) Middleware ---
# Bu, test_stream.html'in (farklı bir "origin") backend'e erişmesine izin verir.
origins = [
    "*", # Geliştirme için şimdilik herkese izin verelim.
    # "http://localhost:5500",
    # "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Tüm metodlara izin ver (GET, POST, etc.)
    allow_headers=["*"], # Tüm header'lara izin ver
)

orchestrator = OrchestratorAgent()


@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "OK", "message": "Exam Evaluator Agent is running."}


# --- API ENDPOINT'LERİ ---

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


# --- YENİ: Hızlı Test İçin Geliştirici Endpoint'i ---
@app.post("/api/dev/start-sample-job", response_model=schemas.JobStatus, tags=["Development"])
async def start_sample_job(background_tasks: BackgroundTasks):
    """
    Her seferinde dosya yüklememek için, `test_files` klasöründeki
    örnek PDF'lerle otomatik olarak bir iş başlatır.
    """
    job = orchestrator.create_job()
    
    # Not: Bu endpoint'in çalışması için projenin ana dizininde 'test_files' klasörü
    # ve içinde answer_key.pdf, student_1.pdf, student_2.pdf dosyaları olmalı.
    # Çalışma dizinine bağlı kalmamak için proje kökünden mutlak path üretelim
    # backend/app/main.py -> parents[2] proje kökü (../..)
    base_path = Path(__file__).resolve().parents[2] / "test_files"
    file_paths = {
        "answer_key": base_path / "answer_key.pdf",
        "student_sheets": [
            base_path / "student_1.pdf",
            base_path / "student_2.pdf",
            base_path / "student_3.pdf",
            base_path / "student_4.pdf",
        ]
    }
    
    if not all(p.exists() for p in [file_paths["answer_key"]] + file_paths["student_sheets"]):
        raise HTTPException(
            status_code=404,
            detail=f"Sample PDF files not found. Looked under: {base_path}"
        )

    background_tasks.add_task(orchestrator.process_job, job.job_id, file_paths)
    return schemas.JobStatus(job_id=job.job_id, status=job.status)


@app.get("/api/jobs/{job_id}/stream", tags=["Jobs"])
async def stream_job_results(job_id: str):
    # Path parametresinden gelebilecek fazladan tırnakları temizle (ekstra güvenlik)
    clean_job_id = job_id.strip().replace('"', '')
    job = orchestrator.jobs.get(clean_job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{clean_job_id}' not found")

    async def event_generator():
        while True:
            event: schemas.StreamEvent = await job.results_queue.get()
            if event is None:
                break
            yield f"data: {event.model_dump_json()}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")