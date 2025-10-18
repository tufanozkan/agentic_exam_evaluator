# backend/app/agents/follow_up_agent.py

import openai
from pathlib import Path
from .. import schemas, config
from .storage_agent import StorageAgent

class FollowUpAgent:
    def __init__(self, storage_agent: StorageAgent):
        self.client = openai.OpenAI(api_key=config.settings.OPENAI_API_KEY)
        self.storage_agent = storage_agent # StorageAgent'ı bir bağımlılık olarak al
        
        prompt_file = Path(__file__).parent.parent.parent / "prompts" / "follow_up_prompt.txt"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def answer_query(self, job_id: str, student_id: str, question_id: str, user_question: str) -> str:
        # 1. İlgili sorunun zenginleştirilmiş sonucunu StorageAgent'tan al
        context_result = self.storage_agent.get_result(job_id, student_id, question_id)
        
        if not context_result:
            return "İlgili soru için bir değerlendirme sonucu bulunamadı."

        # 2. Prompt'u gerçek verilerle doldur (Artık sahte veri yok!)
        prompt = self.prompt_template.format(
            student_id=student_id,
            question_id=question_id,
            question_text=context_result.question_text,
            student_answer_text=context_result.student_answer_text,
            score=context_result.score,
            max_score=context_result.max_score,
            justification=context_result.justification,
            advice_for_full_marks=context_result.advice_for_full_marks,
            user_question=user_question
        )

        # 3. LLM'e soruyu sor ve cevabı döndür
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating follow-up answer: {e}")
            return "Takip sorusuna cevap üretilirken bir hata oluştu."