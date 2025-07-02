# admin.py - Add this to your existing admin configuration

from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'paid_by', 
        'payment_amount', 
        'payment_mode', 
        'no_of_travelers',
        'status', 
        'created_at',
        'processed_by',
        'processed_at'
    ]
    list_filter = [
        'status', 
        'payment_mode', 
        'created_at',
        'processed_at'
    ]
    search_fields = [
        'paid_by__first_name', 
        'paid_by__last_name', 
        'paid_by__email',
        'reference_number'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'processed_at'
    ]
    raw_id_fields = ['paid_by', 'processed_by']
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_amount',
                'payment_mode',
                'no_of_travelers',
                'reference_number'
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'notes'
            )
        }),
        ('User Information', {
            'fields': (
                'paid_by',
                'processed_by',
                'processed_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('paid_by', 'processed_by')
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # If status is being changed, update processed_by and processed_at
            from django.utils import timezone
            obj.processed_by = request.user
            obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)