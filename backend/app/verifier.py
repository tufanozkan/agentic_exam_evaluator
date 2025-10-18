from . import schemas

class VerifierAgent:
    """
    GraderAgent'tan gelen sonuçların kalitesini ve tutarlılığını doğrulayan ajan.
    """
    def verify_grading_result(self, result: schemas.GradingResult) -> schemas.GradingResult:
        """
        Bir GradingResult nesnesini alır, bir dizi kural tabanlı kontrolden geçirir
        ve verifier_status alanını güncelleyerek nesneyi geri döndürür.
        """
        issues = []
        is_valid = True

        # Kural 1: Puan, rubrik toplamına eşit mi?
        rubric_sum = sum(result.rubric_breakdown.values())
        if round(rubric_sum, 2) != round(result.score, 2):
            issues.append(
                f"Score-Rubric mismatch: Rubric sum is {rubric_sum}, but score is {result.score}."
            )
            is_valid = False

        # Kural 2: Puan, negatif veya maksimum puandan yüksek olabilir mi?
        if result.score < 0:
            issues.append(f"Invalid score: Score {result.score} is negative.")
            is_valid = False
        if result.score > result.max_score:
            issues.append(
                f"Invalid score: Score {result.score} is higher than max_score {result.max_score}."
            )
            is_valid = False

        # Kural 3: Gerekçe alanı boş veya çok kısa mı?
        if not result.justification or len(result.justification) < 10:
            issues.append("Justification is missing or too short.")
            is_valid = False
            
        # Sonucu güncelle
        result.verifier_status.valid = is_valid
        result.verifier_status.issues = issues
        
        # Gelecek Planı: Eğer valid değilse, burada bir "düzeltme" (remediation) adımı
        # tetiklenebilir. Örneğin, LLM'e hatalarla birlikte geri gönderip düzeltmesi istenebilir.
        # Bu, jüriye anlatılacak harika bir detay olur.

        return result