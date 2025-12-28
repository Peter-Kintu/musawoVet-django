# byabulimi/admin.py

from django.contrib import admin
from .models import Farmer, Query, Advice

@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    """
    Admin configuration for Farmer profiles.
    Displays key identifiers and allows filtering by region or premium status.
    """
    list_display = ('phone_number', 'get_full_name', 'region', 'language_code', 'is_premium', 'date_joined')
    list_filter = ('is_premium', 'language_code', 'region')
    search_fields = ('phone_number', 'user__first_name', 'user__last_name')
    ordering = ('-date_joined',)

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


class AdviceInline(admin.StackedInline):
    """
    Allows viewing and editing Gemini's Advice directly inside the Query admin page.
    """
    model = Advice
    can_delete = False
    verbose_name_plural = 'AI Diagnosis & Advice'
    fields = ('diagnosis_code', 'confidence_score', 'is_expert_referred', 'localized_advice', 'english_summary')


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Diagnostic Queries.
    Includes the Advice as an inline for a unified view of the diagnosis.
    """
    list_display = ('id', 'farmer', 'detected_crop', 'timestamp', 'get_confidence')
    list_filter = ('detected_crop', 'timestamp')
    search_fields = ('farmer__phone_number', 'detected_crop', 'raw_query_text')
    inlines = [AdviceInline]
    readonly_fields = ('timestamp',)

    def get_confidence(self, obj):
        try:
            return f"{obj.advice.confidence_score * 100}%"
        except (Advice.DoesNotExist, AttributeError):
            return "N/A"
    get_confidence.short_description = 'AI Confidence'


@admin.register(Advice)
class AdviceAdmin(admin.ModelAdmin):
    """
    Standalone admin for Advice if needed for bulk analysis or auditing.
    """
    list_display = ('query', 'diagnosis_code', 'confidence_score', 'is_expert_referred')
    list_filter = ('is_expert_referred', 'diagnosis_code')
    search_fields = ('diagnosis_code', 'english_summary', 'query__farmer__phone_number')