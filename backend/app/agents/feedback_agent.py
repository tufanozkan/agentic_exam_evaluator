# backend/app/agents/feedback_agent.py

import openai
import json
from pathlib import Path
from .. import schemas, config

class FeedbackAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.settings.OPENAI_API_KEY)
        
        current_dir = Path(__file__).parent
        prompt_file = current_dir.parent.parent / "prompts" / "feedback_prompt.txt"

        with open(prompt_file, "r", encoding="utf-8") as f:
            self.feedback_prompt_template = f.read()

    def generate_feedback_for_question(self, grading_result: schemas.GradingResult, student_answer_text: str, question_text: str) -> str:
        prompt = self.feedback_prompt_template.format(
            question_text=question_text,
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
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating feedback: {e}")
            return "Could not generate feedback due to an internal error."