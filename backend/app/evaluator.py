import openai
import json
from typing import Dict, Any
from datetime import datetime

# Şemaları ve ayarları import ediyoruz
from . import schemas
from .config import settings

class GraderAgent:
    def __init__(self):
        # OpenAI istemcisini API anahtarımızla başlatıyoruz
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set!")
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prompt şablonunu dosyadan okuyoruz
        with open("backend/prompts/grader_prompt.txt", "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def grade_question(
        self,
        question: schemas.QuestionObject,
        student_answer: schemas.StudentAnswerObject,
        job_id: str
    ) -> schemas.GradingResult:
        
        # Prompt'ı ilgili bilgilerle dolduruyoruz
        prompt = self.prompt_template.format(
            question_text=question.question_text,
            expected_answer=question.expected_answer,
            max_score=question.max_score,
            rubric=json.dumps(question.rubric),
            student_answer=student_answer.student_answer_text
        )

        llm_raw_response = ""
        llm_response_data = {}
        is_valid = False
        issues = []

        try:
            # OpenAI API'sine çağrı yapıyoruz
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # Hızlı ve uygun maliyetli, güçlü bir model
                messages=[
                    {"role": "system", "content": "You are an expert exam grader AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0, # Tutarlılık için temperature'ı 0 yapıyoruz
                response_format={"type": "json_object"} # JSON çıktısı istediğimizi belirtiyoruz
            )
            llm_raw_response = response.choices[0].message.content
            
            # Gelen cevabı JSON olarak parse etmeye çalışıyoruz
            llm_response_data = json.loads(llm_raw_response)
            
            # Basit bir doğrulama (VerifierAgent'ın MVP'si)
            if sum(llm_response_data.get("rubric_breakdown", {}).values()) != llm_response_data.get("score"):
                 issues.append("Score does not match the sum of rubric_breakdown.")
            else:
                 is_valid = True

        except json.JSONDecodeError:
            issues.append("LLM did not return a valid JSON object.")
        except Exception as e:
            issues.append(f"An unexpected error occurred during LLM call: {str(e)}")

        # Nihai GradingResult objesini oluşturuyoruz
        return schemas.GradingResult(
            job_id=job_id,
            student_id=student_answer.student_id,
            question_id=question.question_id,
            score=llm_response_data.get("score", 0),
            max_score=question.max_score,
            rubric_breakdown=llm_response_data.get("rubric_breakdown", {}),
            justification=llm_response_data.get("justification", "Error during processing."),
            advice_for_full_marks=llm_response_data.get("advice_for_full_marks", ""),
            llm_prompt=prompt,
            llm_raw_response=llm_raw_response,
            model="gpt-4o-mini",
            model_params={"temperature": 0.0, "response_format": {"type": "json_object"}},
            timestamp=datetime.utcnow(),
            verifier_status=schemas.VerifierStatus(valid=is_valid, issues=issues)
        )