from django.db import models
from apps.customers.models import Customer
from .choices import ActivityType, ActivitySource


# Create your models here.
class Activity(models.Model):
    # We keep a per-source external id so we can upsert without duplicates.
    external_id = models.BigIntegerField()
    source = models.CharField(max_length=20, choices=ActivitySource.choices)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
        help_text="May be null if the external system references an unknown customer.",
    )

    type = models.CharField(max_length=20, choices=ActivityType.choices)
    title = models.CharField(max_length=255, blank=True, default="")
    content = models.TextField(blank=True, default="")
    ai_summary = models.TextField(blank=True, default="")
    ai_category = models.CharField(max_length=50, blank=True, default="")
    ai_priority = models.CharField(max_length=20, blank=True, default="")

    # External systems may not provide a timestamp; we store a best-effort.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="uniq_activity_source_external_id",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source}:{self.external_id} ({self.type})"
