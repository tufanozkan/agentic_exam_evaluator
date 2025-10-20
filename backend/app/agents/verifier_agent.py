# backend/app/agents/verifier_agent.py

import json
import openai
from pathlib import Path
from .. import schemas, config
from typing import List


class VerifierAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.settings.OPENAI_API_KEY)
        prompt_file = Path(__file__).parent.parent.parent / "prompts" / "corrector_prompt.txt"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.corrector_prompt_template = f.read()

    def _attempt_correction(self, result: schemas.GradingResult, issues: List[str]) -> schemas.GradingResult:
        """LLM kullanarak hatalı sonucu düzeltmeye çalışır."""
        print(f"--- VerifierAgent: Correction attempt for Q{result.question_id} ---")
        
        prompt = self.corrector_prompt_template.format(
            original_json=result.llm_raw_response, #grader output
            issues="\n- ".join(issues)
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            corrected_data = json.loads(response.choices[0].message.content)

            #update the original result
            corrected_result = result.model_copy(update=corrected_data)
            
            #check status
            new_rubric_sum = sum(corrected_result.rubric_breakdown.values())
            if round(new_rubric_sum, 2) == round(corrected_result.score, 2):
                corrected_result.verifier_status.valid = True
                corrected_result.verifier_status.issues = [] # Sorunları temizle
                corrected_result.verifier_status.was_corrected = True
                print(f"--- VerifierAgent: Correction SUCCESSFUL ---")
            else:
                #keep the original error
                corrected_result.verifier_status.valid = False
                corrected_result.verifier_status.issues.append("Self-correction attempt failed.")
                print(f"--- VerifierAgent: Correction FAILED ---")

            corrected_result.verifier_status.correction_attempts = 1
            return corrected_result

        except Exception as e:
            print(f"--- VerifierAgent: Correction attempt threw an exception: {e} ---")
            #return the original faulty result
            result.verifier_status.correction_attempts = 1
            result.verifier_status.issues.append(f"Self-correction failed with exception: {e}")
            return result


    def verify_grading_result(self, result: schemas.GradingResult) -> schemas.GradingResult:
        issues = []
        is_valid = True

        rubric_sum = sum(result.rubric_breakdown.values())
        if round(rubric_sum, 2) != round(result.score, 2):
            issues.append(f"Score-Rubric mismatch: Rubric sum is {rubric_sum}, but score is {result.score}.")
            is_valid = False

        if result.score < 0:
            issues.append(f"Invalid score: Score {result.score} is negative.")
            is_valid = False
        if result.score > result.max_score:
            issues.append(f"Invalid score: Score {result.score} is higher than max_score {result.max_score}.")
            is_valid = False

        if not result.justification or len(result.justification) < 10:
            issues.append("Justification is missing or too short.")
            is_valid = False
            
        result.verifier_status.valid = is_valid
        result.verifier_status.issues = issues
        
        if not is_valid:
            #if the result is invalid, attempt correction
            return self._attempt_correction(result, issues)

        return result