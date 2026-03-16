from django_filters import rest_framework as filters
from .models import Activity
from .choices import ActivityType, ActivitySource

class ActivityFilter(filters.FilterSet):
    type = filters.ChoiceFilter(field_name="type", choices=ActivityType.choices)
    source = filters.ChoiceFilter(field_name="source", choices=ActivitySource.choices)
    customer_id = filters.NumberFilter(field_name="customer_id")

    class Meta:
        model = Activity
        fields = ["type", "source", "customer_id"]