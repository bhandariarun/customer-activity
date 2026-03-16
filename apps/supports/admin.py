from django.contrib import admin
from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "external_id", "type", "customer", "title", "created_at")
    list_filter = ("source", "type")
    search_fields = ("title", "content")