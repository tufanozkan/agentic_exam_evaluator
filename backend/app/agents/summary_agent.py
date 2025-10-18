# backend/app/agents/summary_agent.py

import openai
import json
from typing import List
from pathlib import Path
from .. import schemas, config

class SummaryAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.settings.OPENAI_API_KEY)
        
        # --- DÜZELTME BURADA ---
        current_dir = Path(__file__).parent
        prompt_file = current_dir.parent.parent / "prompts" / "summary_prompt.txt"

        with open(prompt_file, "r", encoding="utf-8") as f:
            self.summary_prompt_template = f.read()

    def generate_summary_report(self, all_graded_results: List[schemas.GradingResult]) -> str:
        # --- DÜZELTME BURADA: mode='json' EKLENDİ ---
        results_for_prompt = [
            result.model_dump(mode='json', exclude={'llm_prompt', 'llm_raw_response'}) 
            for result in all_graded_results
        ]
        
        prompt = self.summary_prompt_template.format(
            all_graded_results=json.dumps(results_for_prompt, indent=2)
        )
        try:
            # ... (geri kalan kod aynı) ...
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Could not generate summary report due to an internal error."