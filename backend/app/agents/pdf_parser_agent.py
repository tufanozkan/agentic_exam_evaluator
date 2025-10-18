# backend/app/agents/pdf_parser_agent.py

import pdfplumber
import re
from typing import List
from io import BytesIO
from .. import schemas
from .normalizer_agent import NormalizerAgent

class PDFParserAgent:
    def __init__(self):
        #bu sınıfın bir parçası
        self.normalizer = NormalizerAgent()

    def parse_answer_key(self, file_content: bytes) -> List[schemas.QuestionObject]:
        file = BytesIO(file_content)
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    #normalizer agent
                    text += self.normalizer.normalize(page_text) + "\n"

        questions = []
        question_blocks = re.split(r'(?=Soru \d+:)', text)[1:]

        for i, block in enumerate(question_blocks, 1):
            try:
                match = re.match(r'(Soru \d+:.*?[\?\.])(.*)', block, re.DOTALL)
                if match:
                    #normalizer agent
                    question_text = self.normalizer.normalize(match.group(1))
                    expected_answer = self.normalizer.normalize(match.group(2))
                else:
                    question_text = block.split('\n')[0]
                    expected_answer = block.replace(question_text, '')
                
                questions.append(schemas.QuestionObject(
                    question_id=f"Q{i}",
                    question_text=question_text,
                    expected_answer=expected_answer,
                    max_score=10,
                    rubric={"dogruluk_ve_detay": 10},
                    metadata=schemas.PDFMetadata(page=1, raw_confidence=0.90)
                ))
            except Exception as e:
                print(f"Hata: Soru {i} (yeni parser) parse edilemedi. Hata: {e}")
                continue
        return questions

    def parse_student_answers(self, file_content: bytes, student_id: str) -> List[schemas.StudentAnswerObject]:
        file = BytesIO(file_content)
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    #normalizer agent
                    text += self.normalizer.normalize(page_text) + "\n"

        answers = []
        question_blocks = re.split(r'(?=Soru \d+:)', text)[1:]

        for i, block in enumerate(question_blocks, 1):
            try:
                answer_match = re.search(r'Cevap:(.*)', block, re.DOTALL | re.IGNORECASE)
                answer_text = ""
                if answer_match:
                    #normalizer agent
                    answer_text = self.normalizer.normalize(answer_match.group(1))
                
                answers.append(schemas.StudentAnswerObject(
                    student_id=student_id,
                    question_id=f"Q{i}",
                    student_answer_text=answer_text,
                    metadata=schemas.OCRMetadata(page=1, ocr_confidence=0.88)
                ))
            except Exception as e:
                print(f"Hata: Öğrenci {student_id}, Soru {i} (yeni parser) parse edilemedi. Hata: {e}")
                continue
        return answers