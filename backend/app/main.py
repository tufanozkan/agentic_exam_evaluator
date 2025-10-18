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
from .reporting import ReportingAgent # YENİ

# Ajan nesnelerini oluşturuyoruz
grader = GraderAgent()
reporter = ReportingAgent() # YENİ

# ... (@app.get("/") ve diğer endpoint'ler aynı kalacak) ...

@app.post("/api/test/grade-single-full-flow", response_model=schemas.FinalReport, tags=["Testing"])
async def test_grade_single_full_flow(
    answer_key_pdf: UploadFile = File(...),
    student_sheet_pdf: UploadFile = File(...)
):
    """
    Test amacıyla tam bir akışı çalıştırır: Parse -> Grade -> Feedback -> Summary.
    Tek bir soru üzerinden tüm ajanların çıktısını birleştirerek nihai bir rapor döner.
    """
    # 1. Parse Agent
    question_objects = parse_answer_key(answer_key_pdf.file)
    student_answers = parse_student_answers(student_sheet_pdf.file, student_id="test_student_01")

    # (Bu kısım MVP için basitleştirilmiştir. Normalde tüm sorular döngüye girer.)
    first_question = question_objects[0]
    first_answer = student_answers[0]
    
    # 2. Grader Agent
    job_id = "test_job_full_flow"
    grading_result = grader.grade_question(first_question, first_answer, job_id)

    # 3. Feedback Agent
    feedback_text = reporter.generate_feedback_for_question(
        grading_result=grading_result,
        student_answer_text=first_answer.student_answer_text
    )
    question_feedback = schemas.QuestionFeedback(
        question_id=first_question.question_id,
        feedback_text=feedback_text,
        grading_result=grading_result
    )

    # 4. Summary Agent (tek soru üzerinden simülasyon)
    summary_text = reporter.generate_summary_report(all_graded_results=[grading_result])
    
    # 5. Nihai Raporu Oluştur
    final_report = schemas.FinalReport(
        job_id=job_id,
        student_id="test_student_01",
        overall_score=grading_result.score,
        max_score=grading_result.max_score,
        summary_report_text=summary_text,
        question_feedbacks=[question_feedback]
    )
    
    return final_report