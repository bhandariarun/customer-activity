from services.ai.types import AIClassification

class NullAIClassifier:
    def classify(self, title: str, content: str) -> AIClassification:
        # minimal safe fallback
        summary = (content or title or "").strip()[:200]
        return AIClassification(summary=summary, category="other", priority="low")