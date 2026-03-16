from django.db import models


# Create your models here.
class Customer(models.Model):
    # We store the external CRM user id as our primary key to simplify idempotent upserts.
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id} - {self.name}"
