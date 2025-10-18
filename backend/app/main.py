from fastapi import FastAPI, UploadFile, File, Form
from typing import List, Optional
import uuid

# Az önce oluşturduğumuz şemaları import ediyoruz
from . import schemas

# FastAPI uygulamasını oluşturuyoruz
app = FastAPI(
    title="AI-Driven Exam Evaluator Agent",
    description="An agentic system for automated exam assessment with explainability.",
    version="0.1.0"
)

# --- Geçici In-Memory Veritabanı ---
# StorageAgent'in MVP versiyonu. İşlerin durumunu takip eder.
jobs_db = {}


@app.get("/", tags=["Health Check"])
async def read_root():
    """Sistemin ayakta olup olmadığını kontrol eden basit bir endpoint."""
    return {"status": "OK", "message": "Exam Evaluator Agent is running."}

# --- API Endpoint İskeletleri ---

@app.post("/api/jobs", status_code=202, tags=["Jobs"])
async def create_assessment_job(
    answer_key: UploadFile = File(...),
    student_sheets: List[UploadFile] = File(...)
) -> dict:
    """
    Cevap anahtarını ve öğrenci kağıtlarını yükleyerek yeni bir değerlendirme işi başlatır.
    Hemen bir job_id döner, işleme arka planda başlar.
    """
    job_id = str(uuid.uuid4())
    jobs_db[job_id] = {"status": "pending", "files": [f.filename for f in student_sheets]}
    
    # TODO: Arka plan görevini burada başlat (OrchestratorAgent'ı tetikle)
    print(f"Job created with ID: {job_id}")
    
    return {"job_id": job_id, "status": "Job accepted and processing started."}


@app.get("/api/jobs/{job_id}/stream", tags=["Jobs"])
async def stream_job_results(job_id: str):
    """
    Belirtilen işin sonuçlarını Server-Sent Events (SSE) ile canlı olarak yayınlar.
    Frontend bu endpoint'i dinleyerek sonuçları anlık gösterir.
    """
    # TODO: StreamerAgent'ın mantığını buraya implemente et.
    return {"status": "streaming_endpoint_ready", "job_id": job_id}


@app.post("/api/followup/{job_id}/{student_id}/{question_id}", tags=["Explainability"])
async def handle_followup_query(
    job_id: str,
    student_id: str,
    question_id: str,
    query: schemas.GradingResult # Örnek, burası daha basit bir model olabilir
) -> dict:
    """
    Bir değerlendirme sonucuna ilişkin takip sorularını cevaplar. ("Neden 8 aldım?")
    """
    # TODO: FollowUpQueryAgent'ın mantığını buraya implemente et.
    return {"explanation": "Follow-up response will be generated here."}






# backend/app/main.py dosyasının altına ekle

# Ajanlarımızı import ediyoruz
from .parser import parse_answer_key, parse_student_answers
from .evaluator import GraderAgent

# GraderAgent'tan bir nesne oluşturuyoruz
grader = GraderAgent()

@app.post("/api/test/grade-single", tags=["Testing"])
async def test_grade_single(
    answer_key_pdf: UploadFile = File(...),
    student_sheet_pdf: UploadFile = File(...)
):
    """
    Test amacıyla tek bir öğrenci kağıdını ve cevap anahtarını alıp,
    ilk soruyu notlandırır ve sonucu direkt döner.
    """
    # 1. PDF'leri parse et
    question_objects = parse_answer_key(answer_key_pdf.file)
    student_answers = parse_student_answers(student_sheet_pdf.file, student_id="test_student_01")

    if not question_objects or not student_answers:
        return {"error": "Could not parse questions or answers from PDFs."}
        
    # 2. İlk soruyu ve cevabı eşleştir
    first_question = question_objects[0]
    first_answer = next((ans for ans in student_answers if ans.question_id == first_question.question_id), None)

    if not first_answer:
        return {"error": "No matching answer found for the first question."}

    # 3. GraderAgent'ı çağır ve notlandır
    job_id = "test_job_123"
    grading_result = grader.grade_question(first_question, first_answer, job_id)
    
    return grading_result