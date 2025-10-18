# backend/app/agents/normalizer_agent.py

import re

class NormalizerAgent:
    def normalize(self, text: str) -> str:
        """Metindeki fazla boşlukları temizler ve standart hale getirir."""
        if not text:
            return ""
        # Birden fazla boşluğu ve satır sonunu tek boşluğa indirge
        text = re.sub(r'\s+', ' ', text)
        return text.strip()