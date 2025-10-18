# backend/app/agents/follow_up_agent.py

import openai
from pathlib import Path
from .. import schemas, config
from .storage_agent import StorageAgent

class FollowUpAgent:
    def __init__(self, storage_agent: StorageAgent):
        self.client = openai.OpenAI(api_key=config.settings.OPENAI_API_KEY)
        self.storage_agent = storage_agent
        
        prompt_file = Path(__file__).parent.parent.parent / "prompts" / "follow_up_prompt.txt"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def _format_history_for_prompt(self, history):
        if not history:
            return "No previous conversation."
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

    # backend/app/agents/follow_up_agent.py

    def answer_query(self, job_id: str, student_id: str, question_id: str, user_question: str) -> str:
        # 1. Gerekli tüm bağlamı StorageAgent'tan al
        context_result = self.storage_agent.get_result(job_id, student_id, question_id)
        chat_history = self.storage_agent.get_chat_history(job_id, student_id, question_id)

        if not context_result:
            return "İlgili soru için bir değerlendirme sonucu bulunamadı."
            
        # 2. Yeni kullanıcı mesajını geçmişe ekle
        chat_history.append({"role": "user", "content": user_question})
        
        # 3. Prompt'u DOLDUR (Tüm ilgili alanları ekleyerek)
        prompt = self.prompt_template.format(
            # --- GÜNCELLEME: Tüm alanları ekleyerek daha sağlam hale getirelim ---
            question_text=context_result.question_text,
            student_answer_text=context_result.student_answer_text,
            score=context_result.score,
            max_score=context_result.max_score,
            justification=context_result.justification,
            advice_for_full_marks=context_result.advice_for_full_marks, # Bu alan eksikti
            history=self._format_history_for_prompt(chat_history),
            user_question=user_question,
            # Prompt dosyasında olmasa bile fazladan göndermek sorun yaratmaz
            student_id=student_id,
            question_id=question_id
        )

        # 4. LLM'e soruyu sor
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            ai_response = response.choices[0].message.content.strip()
            
            # 5. AI'ın cevabını da geçmişe ekle ve kaydet
            chat_history.append({"role": "ai", "content": ai_response})
            self.storage_agent.save_chat_history(job_id, student_id, question_id, chat_history)
            
            return ai_response
        except Exception as e:
            # Hata durumunda, son eklenen kullanıcı mesajını geri al
            chat_history.pop()
            print(f"Error generating follow-up answer: {e}")
            return "Takip sorusuna cevap üretilirken bir hata oluştu."