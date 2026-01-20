from django.contrib import admin
from .models import APIKey, Package, HomePage, ContactUs, GalleryImage


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
    list_display = ('name', 'email', 'phone', 'package_type', 'created_at')
    list_filter = ['created_at']
    search_fields = ('name', 'email', 'phone', 'message')
    readonly_fields = ('created_at',)  # Assuming 'created_at' is a DateTimeField in your ContactUs model
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'package_type', 'message')
        }),
        ('API Key Info', {
            'fields': ('api_key', 'submitted_by_user'),
            'classes': ('collapse',)  # Optional: To collapse this section initially
        }),
        ('Date Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)  # Optional: To collapse this section initially
        }),
    )

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_active', 'created_at')
    list_filter = ('is_active', 'user', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
