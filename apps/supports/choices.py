from django.db import models


class ActivityType(models.TextChoices):
    TICKET = "ticket", "ticket"
    NOTE = "note", "note"
    EVENT = "event", "event"


class ActivitySource(models.TextChoices):
    CRM = "crm", "crm"
    SUPPORT = "support", "support"
