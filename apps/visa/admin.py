# admin.py
from django.contrib import admin
from .models import VisaApplication, VisaDocument

@admin.register(VisaApplication)
class VisaApplicationAdmin(admin.ModelAdmin):
    list_display = ['application_number', 'applicant_name', 'visa_type', 'status', 'total_fee', 'created_at']
    list_filter = ['status', 'visa_type', 'destination_country']
    search_fields = ['application_number', 'applicant_name', 'passport_number']

@admin.register(VisaDocument)
class VisaDocumentAdmin(admin.ModelAdmin):
    list_display = ['visa_application', 'document_type', 'is_verified', 'created_at']
    list_filter = ['document_type', 'is_verified']
