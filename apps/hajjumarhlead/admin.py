from django.contrib import admin
from .models import HajjUmrahBookingDemo, HajjUmrahBookingService


@admin.register(HajjUmrahBookingDemo)
class HajjUmrahBookingDemoAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'business_plan', 'selected_date', 'created_at']
    list_filter = ['business_plan', 'selected_date', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(HajjUmrahBookingService)
class HajjUmrahBookingServiceAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'business_plan', 'created_at']
    list_filter = ['business_plan', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
