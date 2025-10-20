# backend/app/agents/pdf_parser_agent.py

import pdfplumber
import re
import json
import openai
from typing import List
from io import BytesIO
from pathlib import Path
from .. import schemas, config
from .normalizer_agent import NormalizerAgent

class PDFParserAgent:
    def __init__(self):
        self.normalizer = NormalizerAgent()
        
        self.client = openai.OpenAI(api_key=config.settings.OPENAI_API_KEY)
        prompt_file = Path(__file__).parent.parent.parent / "prompts" / "parser_prompt.txt"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.parser_prompt_template = f.read()

    def parse_answer_key(self, file_content: bytes) -> List[schemas.QuestionObject]:
        #extract questions and answers
        file = BytesIO(file_content)
        raw_text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=1, y_tolerance=3)
                if page_text:
                    raw_text += page_text + "\n"
        
        prompt = self.parser_prompt_template.format(raw_text=raw_text)
        
        questions = []
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            response_data = json.loads(response.choices[0].message.content)
            
            #key or list?
            if isinstance(response_data, dict):
                #(example 'questions', 'data', veya first key))
                key_to_list = next((k for k in response_data if isinstance(response_data[k], list)), None)
                if key_to_list:
                    extracted_list = response_data[key_to_list]
                else:
                    raise ValueError("LLM response did not contain a JSON array.")
            elif isinstance(response_data, list):
                extracted_list = response_data
            else:
                raise ValueError("LLM response is not a valid JSON array or object containing an array.")

            for item in extracted_list:
                questions.append(schemas.QuestionObject(
                    question_id=item.get("question_id"),
                    question_text=self.normalizer.normalize(item.get("question_text")),
                    expected_answer=self.normalizer.normalize(item.get("expected_answer")),
                    max_score=10,
                    rubric={"dogruluk_ve_detay": 10},
                    metadata=schemas.PDFMetadata(page=1, raw_confidence=0.98) #trust score
                ))
        
        except Exception as e:
            print(f"Hata: LLM tabanlı cevap anahtarı parse edilirken sorun oluştu. Hata: {e}")
            return []
            
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