#backend/app/main.py

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path

from . import schemas
from fastapi import WebSocket
from .services.connection_manager import manager
from .orchestrator import OrchestratorAgent
from .services.streamer_service import Job
from .agents.follow_up_agent import FollowUpAgent #last added
import asyncio

app = FastAPI(
    title="AI-Driven Exam Evaluator Agent",
    description="An agentic system for automated exam assessment with explainability.",
    version="1.0.0"
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#one orchestrator
orchestrator = OrchestratorAgent()
follow_up_agent = FollowUpAgent(storage_agent=orchestrator.storage_agent)

class FollowUpQuery(schemas.BaseModel):
    query: str


@app.post("/api/followup/{job_id}/{student_id}/{question_id}", tags=["Explainability"])
async def handle_followup_query(
    job_id: str,
    student_id: str,
    question_id: str,
    request: FollowUpQuery
):
    try:
        answer = await asyncio.to_thread(
            follow_up_agent.answer_query,
            job_id, student_id, question_id, request.query
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    #root
    project_root = Path(__file__).parent.parent.parent
    base_path = project_root / "test_files"
    
    file_paths = {
        "answer_key": base_path / "answer_key.pdf",
        "student_sheets": [
            base_path / "student_1.pdf", base_path / "student_2.pdf",
            base_path / "student_3.pdf", base_path / "student_4.pdf",
        ]
    }
    
    if not all(p.exists() for p in [file_paths["answer_key"]] + file_paths["student_sheets"]):
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

@app.websocket("/api/jobs/{job_id}/ws")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        #connection is open and waiting
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(job_id)