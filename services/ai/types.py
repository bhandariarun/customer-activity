from dataclasses import dataclass

@dataclass(frozen=True)
class AIClassification:
    summary: str
    category: str   # billing|technical|configuration|integration|other
    priority: str   # low|medium|high