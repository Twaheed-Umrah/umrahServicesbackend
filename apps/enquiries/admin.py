from django.contrib import admin
from .models import APIKey, Package, HomePage, ContactUs


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'key', 'is_active', 'created_at', 'last_used', 'website_url')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'name', 'key', 'website_url')
    readonly_fields = ('created_at', 'last_used', 'key')


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'package_type', 'price', 'currency', 'duration_days', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'package_type')
    search_fields = ('title', 'description', 'features')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('package_type', 'title', 'description', 'price', 'currency', 'duration_days')
        }),
        ('Media & Features', {
            'fields': ('image', 'features')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    list_display = ('welcome_title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('welcome_title', 'welcome_subtitle', 'content')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'package_type', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('created_at',)
