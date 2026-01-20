from django.contrib import admin
from .models import Lead, LeadNote

class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 1
    readonly_fields = ('created_at',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'status', 'user', 'created_at', 'updated_at')
    list_filter = ('status', 'user', 'created_at')
    search_fields = ('name', 'mobile_number', 'email', 'user__username')
    inlines = [LeadNoteInline]
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'note', 'created_at')
    list_filter = ('created_at', 'lead__user')
    search_fields = ('note', 'lead__name')