from __future__ import annotations

from celery import shared_task
from django.db import transaction
import time

from apps.supports.models import Activity
from services.ai.factory import get_ai_classifier


@shared_task(bind=True, queue="ai", max_retries=8)
def classify_activities_ai_batch(self, activity_ids: list[int]) -> None:
    """
    Classify a batch of activities to reduce task overhead and control rate.
    Retries with backoff on rate limits / transient errors.
    """
    try:
        classifier = get_ai_classifier()

        # Fetch only what we need, skip already-classified
        activities = list(
            Activity.objects.filter(id__in=activity_ids)
        )

        for a in activities:
            if a.ai_summary and a.ai_category and a.ai_priority:
                continue

            try:
                classification = classifier.classify(title=a.title, content=a.content)
            except Exception as exc:
                # If we get rate-limited, back off and retry the whole batch
                # (simple approach; you can get fancy per-item if needed)
                countdown = min(600, 2 ** self.request.retries * 5)  # 5s, 10s, 20s, ...
                raise self.retry(exc=exc, countdown=countdown)

            with transaction.atomic():
                locked = Activity.objects.select_for_update().get(id=a.id)
                if locked.ai_summary and locked.ai_category and locked.ai_priority:
                    continue
                locked.ai_summary = classification.summary
                locked.ai_category = classification.category
                locked.ai_priority = classification.priority
                locked.save(update_fields=["ai_summary", "ai_category", "ai_priority"])

            # tiny sleep to be polite; tune as needed (e.g. 0.2–0.5s)
            time.sleep(0.2)

    except Exception as exc:
        countdown = min(600, 2 ** self.request.retries * 5)
        raise self.retry(exc=exc, countdown=countdown)