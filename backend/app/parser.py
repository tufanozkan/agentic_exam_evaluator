import pdfplumber
import re
from typing import List, IO
from . import schemas

def parse_answer_key(file: IO[bytes]) -> List[schemas.QuestionObject]:
    """
    Cevap anahtarı PDF'ini okur ve yapısal QuestionObject listesi döndürür.
    MVP için basit bir format varsayıyoruz.
    Örnek Format:
    Soru 1:
    [Metin]
    ---
    Cevap: [Anahtar Cümleler]
    ---
    Puan: 10
    ---
    Rubrik: {"konsept": 5, "detay": 5}
    """
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    questions = []
    # Soruları "Soru X:" kalıbına göre ayırıyoruz
    question_blocks = re.split(r'Soru \d+:', text)[1:] 

    for i, block in enumerate(question_blocks, 1):
        try:
            # Her bloğu "---" ile ayırıp parçaları alıyoruz
            parts = [p.strip() for p in block.split('---')]
            question_text = parts[0]
            expected_answer = parts[1].replace('Cevap:', '').strip()
            max_score = int(parts[2].replace('Puan:', '').strip())
            # Rubrik'i JSON'dan Python dict'ine çeviriyoruz
            import json
            rubric_str = parts[3].replace('Rubrik:', '').strip()
            rubric = json.loads(rubric_str)

            questions.append(schemas.QuestionObject(
                question_id=f"Q{i}",
                question_text=question_text,
                expected_answer=expected_answer,
                max_score=max_score,
                rubric=rubric,
                metadata=schemas.PDFMetadata(page=1, raw_confidence=0.95) # Mock data
            ))
        except Exception as e:
            print(f"Hata: Soru {i} parse edilemedi. Blok: {block[:100]}... Hata: {e}")
            continue # Hatalı bloğu atla
            
    return questions

def parse_student_answers(file: IO[bytes], student_id: str) -> List[schemas.StudentAnswerObject]:
    """Öğrenci cevap kağıdını okur ve yapısal StudentAnswerObject listesi döndürür."""
    # Bu fonksiyon da benzer bir mantıkla çalışır. Şimdilik basit tutalım.
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    answers = []
    answer_blocks = re.split(r'Soru \d+:', text)[1:]

    for i, block in enumerate(answer_blocks, 1):
        answers.append(schemas.StudentAnswerObject(
            student_id=student_id,
            question_id=f"Q{i}",
            student_answer_text=block.strip(),
            metadata=schemas.OCRMetadata(page=1, ocr_confidence=0.90) # Mock data
        ))
        
    return answers