from typing import Optional
from rest_framework import serializers
from .models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    customer_id = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id",
            "external_id",
            "customer_id",
            "type",
            "title",
            "content",
            "source",
            "ai_summary",
            "ai_category",
            "ai_priority",
            "created_at",
        ]

    def get_customer_id(self, obj: Activity) -> Optional[int]:
        return obj.customer_id
