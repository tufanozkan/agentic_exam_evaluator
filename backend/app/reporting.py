import openai
import json
from pathlib import Path
from typing import List

from . import schemas
from .config import settings

class ReportingAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prompt şablonlarını yükle
        current_dir = Path(__file__).parent  # reporting.py'nin bulunduğu klasör
        prompt_file = current_dir.parent / "prompts" / "feedback_prompt.txt"
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.feedback_prompt_template = f.read()

        current_dir = Path(__file__).parent  # reporting.py'nin bulunduğu klasör
        prompt_file = current_dir.parent / "prompts" / "summary_prompt.txt"
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.summary_prompt_template = f.read()

    def generate_feedback_for_question(self, grading_result: schemas.GradingResult, student_answer_text: str) -> str:
        """Tek bir soru için LLM kullanarak öğrenci dostu geri bildirim üretir."""
        prompt = self.feedback_prompt_template.format(
            question_text="...", # Not: Bu bilgiyi grading_result'a eklemek veya context'ten almak gerekebilir. Şimdilik mock.
            student_answer_text=student_answer_text,
            score=grading_result.score,
            max_score=grading_result.max_score,
            justification=grading_result.justification,
            advice_for_full_marks=grading_result.advice_for_full_marks,
            rubric_breakdown=json.dumps(grading_result.rubric_breakdown)
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2 # Biraz daha yaratıcı bir dil için hafifçe artırabiliriz
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating feedback: {e}")
            return "Could not generate feedback due to an internal error."

    def generate_summary_report(self, all_graded_results: List[schemas.GradingResult]) -> str:
        """Bir öğrencinin tüm notlarını alıp genel bir özet rapor üretir."""
        
        # LLM'e göndermek için sonuçları daha okunabilir bir formata getirelim
        # Not: Pydantic v2'de mode="json" kullanmak datetime gibi tipleri JSON'a uygun değerlere (ISO 8601 string) dönüştürür
        results_for_prompt = [
            result.model_dump(mode="json", exclude={'llm_prompt', 'llm_raw_response'})
            for result in all_graded_results
        ]
        
        prompt = self.summary_prompt_template.format(
            all_graded_results=json.dumps(results_for_prompt, indent=2)
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Could not generate summary report due to an internal error."