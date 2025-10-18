import pdfplumber
import re
from typing import List, IO
from . import schemas
from io import BytesIO

def parse_answer_key(file_content: bytes) -> List[schemas.QuestionObject]:
    file = BytesIO(file_content)
    """
    Yeniden tasarlanmış parser. Cevap anahtarı PDF'ini okur ve yapısal QuestionObject listesi döndürür.
    Artık '---' ayraçlarına değil, metin akışına göre soru ve cevabı ayırır.
    Puan ve Rubrik bilgisi PDF'te olmadığı için varsayılan değerler atanır.
    """
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            # Daha temiz metin için birden fazla boşluğu tek boşluğa indirge
            page_text = page.extract_text()
            if page_text:
                text += re.sub(r'\s+', ' ', page_text) + "\n"

    questions = []
    # Pozitif lookbehind ile ayırma: "Soru X:" kalıbını kaybetmeden bloklara ayır
    question_blocks = re.split(r'(?=Soru \d+:)', text)[1:]

    for i, block in enumerate(question_blocks, 1):
        try:
            # Soru metni genellikle ilk satırdır veya ? ile biter.
            # İlk satırı soru olarak alalım, geri kalanı cevap.
            lines = block.strip().split('\n', 1)
            question_text = lines[0].strip()
            
            # Geri kalan metnin tamamını beklenen cevap olarak al
            expected_answer = ""
            if len(lines) > 1:
                expected_answer = lines[1].strip()

            # Eğer soru ve cevap ayrımı net değilse, daha basit bir regex deneyebiliriz.
            # Örneğin, ilk cümleyi soru, geri kalanı cevap olarak alabiliriz.
            match = re.match(r'(Soru \d+:.*?[\?\.])(.*)', block, re.DOTALL)
            if match:
                question_text = match.group(1).strip()
                expected_answer = match.group(2).strip()

            if not expected_answer: # Eğer cevap boş kaldıysa tüm bloğu cevap olarak ata
                expected_answer = block.replace(question_text, '').strip()

            questions.append(schemas.QuestionObject(
                question_id=f"Q{i}",
                question_text=question_text,
                expected_answer=expected_answer,
                # EKSİK BİLGİ: PDF'te olmadığı için varsayılan değerler atıyoruz
                max_score=10,
                rubric={"dogruluk_ve_detay": 10},
                metadata=schemas.PDFMetadata(page=1, raw_confidence=0.90) # Güven %90 diyelim
            ))
        except Exception as e:
            print(f"Hata: Soru {i} (yeni parser) parse edilemedi. Hata: {e}")
            continue
            
    return questions

def parse_student_answers(file_content: bytes, student_id: str) -> List[schemas.StudentAnswerObject]:
    file = BytesIO(file_content)
    """
    Yeniden tasarlanmış öğrenci cevap parser'ı.
    "Soru X:" ve "Cevap:" anahtar kelimelerini arar.
    """
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += re.sub(r'\s+', ' ', page_text) + "\n"

    answers = []
    question_blocks = re.split(r'(?=Soru \d+:)', text)[1:]

    for i, block in enumerate(question_blocks, 1):
        try:
            # "Cevap:" kelimesinden sonraki kısmı öğrencinin cevabı olarak al
            answer_match = re.search(r'Cevap:(.*)', block, re.DOTALL | re.IGNORECASE)
            answer_text = ""
            if answer_match:
                answer_text = answer_match.group(1).strip()
            
            if not answer_text: # Eğer "Cevap:" bulunamazsa, Soru metninden sonrasını al
                question_text_match = re.match(r'(Soru \d+:.*?[\?\.])(.*)', block, re.DOTALL)
                if question_text_match:
                    answer_text = question_text_match.group(2).strip()

            answers.append(schemas.StudentAnswerObject(
                student_id=student_id,
                question_id=f"Q{i}",
                student_answer_text=answer_text,
                metadata=schemas.OCRMetadata(page=1, ocr_confidence=0.88) # Mock data
            ))
        except Exception as e:
            print(f"Hata: Öğrenci {student_id}, Soru {i} (yeni parser) parse edilemedi. Hata: {e}")
            continue
        
    return answers