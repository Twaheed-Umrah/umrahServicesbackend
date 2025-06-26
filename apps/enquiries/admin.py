from django.contrib import admin
from .models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'place', 'agency', 'franchise', 'created_at']
    list_filter = ['created_at', 'updated_at', 'place', 'agency', 'franchise']
    search_fields = ['name', 'email', 'phone', 'message', 'place']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'place')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Assignment', {
            'fields': ('agency', 'franchise'),
            'description': 'Assign this enquiry to an agency or franchise.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Optional: Add ordering
    ordering = ['-created_at']
    
    # Optional: Add date hierarchy for better navigation
    date_hierarchy = 'created_at'
    
    # Optional: Customize the change list template
    actions_on_top = True
    actions_on_bottom = False
    
    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        return super().get_queryset(request).select_related('agency', 'franchise')