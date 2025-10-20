from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from typing import Union

#nerden geliyor, ne kadar güvenli vs..

class PDFMetadata(BaseModel):
    page: int
    raw_confidence: float = Field(..., ge=0.0, le=1.0)

class OCRMetadata(BaseModel):
    page: int
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)

class VerifierStatus(BaseModel):
    valid: bool
    issues: List[str] = []
    was_corrected: bool = False
    correction_attempts: int = 0
    suggested_correction: Optional[Dict[str, Any]] = None


#agents 
class QuestionObject(BaseModel):
    """PDFParserAgent tarafından üretilen, bir sorunun yapısal temsili."""
    question_id: str
    question_text: str
    expected_answer: str
    max_score: int
    rubric: Dict[str, int]
    metadata: PDFMetadata

class StudentAnswerObject(BaseModel):
    """PDFParserAgent tarafından öğrenci kağıdından ayrıştırılan cevap."""
    student_id: str
    question_id: str
    student_answer_text: str
    metadata: OCRMetadata

class GradingResult(BaseModel):
    """
    Sistemdeki en önemli veri yapısı. Bir sorunun değerlendirme sonucunu,
    açıklamasını ve denetim (audit) bilgilerini içerir.
    """
    job_id: str
    student_id: str
    question_id: str
    score: float
    max_score: int
    question_text: str
    student_answer_text: str
    expected_answer: str
    rubric_breakdown: Dict[str, float]
    justification: str
    advice_for_full_marks: str
    llm_prompt: str
    llm_raw_response: str
    model: str
    model_params: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    verifier_status: VerifierStatus

class QuestionFeedback(BaseModel):
    """Tek bir soru için üretilen zenginleştirilmiş geri bildirim."""
    question_id: str
    feedback_text: str
    grading_result: GradingResult

class FinalReport(BaseModel):
    """Bir öğrenci için oluşturulan nihai rapor."""
    job_id: str
    student_id: str
    overall_score: float
    max_score: float
    summary_report_text: str
    question_feedbacks: List[QuestionFeedback]

class StreamEvent(BaseModel):
    """
    SSE (Server-Sent Events) ile frontend'e gönderilecek standart event yapısı.
    """
    event: str # Örn: "partial_result", "student_done", "job_done", "error"
    data: Dict[str, Any]

class JobStatus(BaseModel):
    job_id: str
    status: str

class FollowUpQuery(BaseModel):
    query: str