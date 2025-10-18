from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- Metadata Alt Modelleri ---
# Bu modeller, verinin nereden geldiğini ve ne kadar güvenilir olduğunu belirtir.

class PDFMetadata(BaseModel):
    page: int
    raw_confidence: float = Field(..., ge=0.0, le=1.0)

class OCRMetadata(BaseModel):
    page: int
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)

class VerifierStatus(BaseModel):
    valid: bool
    issues: List[str] = []
    suggested_correction: Optional[Dict[str, Any]] = None

# --- Ana Agent Kontratları ---

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
    rubric_breakdown: Dict[str, float]
    justification: str
    advice_for_full_marks: str
    
    # Denetim (Audit Trail) Alanları - Jüri için kritik!
    llm_prompt: str
    llm_raw_response: str
    model: str
    model_params: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    verifier_status: VerifierStatus