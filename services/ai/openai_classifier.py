import json
import os
import requests

from services.ai.types import AIClassification


class OpenAIClassifier:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini", timeout: float = 20.0):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

    def classify(self, title: str, content: str) -> AIClassification:
        prompt = f"""
You are classifying a customer activity. Return ONLY valid JSON with keys:
summary, category, priority.

category must be one of: billing, technical, configuration, integration, other
priority must be one of: low, medium, high

Title: {title}
Content: {content}
""".strip()

        url = "https://api.openai.com/v1/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": prompt,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        # Extract text output from Responses API
        # (This is best-effort; keep it defensive)
        text = ""
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text += c.get("text", "")

        text = text.strip()
        parsed = json.loads(text)

        return AIClassification(
            summary=str(parsed.get("summary", "")).strip(),
            category=str(parsed.get("category", "other")).strip(),
            priority=str(parsed.get("priority", "low")).strip(),
        )