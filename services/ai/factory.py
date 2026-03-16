import os

from services.ai.null_classifier import NullAIClassifier

def get_ai_classifier():
    provider = os.getenv("AI_PROVIDER", "none").lower()

    if provider == "openai":
        from services.ai.openai_classifier import OpenAIClassifier
        return OpenAIClassifier()

    return NullAIClassifier()