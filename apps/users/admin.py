# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import User, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Display fields in list view
    list_display = (
        'username', 'email', 'get_full_name_display', 'role', 
        'phone', 'company_name', 'is_active', 'is_staff', 
        'profile_image_preview', 'date_joined'
    )
    
    # Add filters
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_superuser', 
        'date_joined', 'last_login', 'created_by'
    )
    
    # Add search functionality
    search_fields = (
        'username', 'email', 'first_name', 'last_name', 
        'phone', 'company_name'
    )
    
    # Order by date joined (newest first)
    ordering = ('-date_joined',)
    
    # Fields to display in detail view - Updated for merged model
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'profile_image')
        }),
        ('Profile Information', {
            'fields': ('bio', 'website'),
            'classes': ('collapse',)
        }),
        ('Company Information', {
            'fields': ('company_name', 'company_logo'),
            'classes': ('collapse',)
        }),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Relationships', {
            'fields': ('created_by',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    # Fields to display when adding new user - Updated for merged model
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone', 'address', 'profile_image')
        }),
        ('Profile Information', {
            'fields': ('bio', 'website'),
            'classes': ('collapse',)
        }),
        ('Company Information', {
            'fields': ('company_name', 'company_logo'),
            'classes': ('collapse',)
        }),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'created_by')
        }),
    )
    
    # Readonly fields for timestamps
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at')
    
    # Actions
    actions = ['activate_users', 'deactivate_users', 'export_users_csv']
    
    def get_full_name_display(self, obj):
        """Display full name or username if no first/last name"""
        full_name = obj.get_full_name()
        return full_name if full_name.strip() else obj.username
    get_full_name_display.short_description = 'Full Name'
    
    def profile_image_preview(self, obj):
        """Display profile image thumbnail"""
        if obj.profile_image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                obj.profile_image.url
            )
        return "No Image"
    profile_image_preview.short_description = 'Profile Image'
    
    def activate_users(self, request, queryset):
        """Custom action to activate users"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} users were successfully activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Custom action to deactivate users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} users were successfully deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def export_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'First Name', 'Last Name', 'Role', 
            'Phone', 'Company Name', 'License Number', 'Is Active', 'Date Joined'
        ])
        
        for user in queryset:
            writer.writerow([
                user.username, user.email, user.first_name, user.last_name,
                user.get_role_display(), user.phone, user.company_name,
                user.license_number, user.is_active, user.date_joined
            ])
        
        return response
    export_users_csv.short_description = "Export selected users to CSV"


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'verification_type', 'new_value', 'otp_display', 'otp_status', 
        'expires_at', 'created_at'
    )
    list_filter = (
        'verification_type', 'is_verified', 'expires_at', 'created_at'
    )
    search_fields = ('user__username', 'user__email', 'new_value')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'verification_type', 'new_value')
        }),
        ('OTP Details', {
            'fields': ('otp', 'expires_at', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def otp_display(self, obj):
        """Display OTP with masking for security"""
        if obj.otp:
            return f"***{obj.otp[-2:]}"  # Show only last 2 digits
        return "No OTP"
    otp_display.short_description = 'OTP'
    
    def otp_status(self, obj):
        """Display OTP status with color coding"""
        if obj.is_verified:
            return format_html('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        elif obj.is_expired():
            return format_html('<span style="color: red; font-weight: bold;">✗ Expired</span>')
        else:
            time_left = obj.expires_at - timezone.now()
            minutes_left = int(time_left.total_seconds() / 60)
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ Pending ({} min left)</span>',
                minutes_left if minutes_left > 0 else 0
            )
    otp_status.short_description = 'Status'
    
    # Actions
    actions = ['mark_as_verified', 'mark_as_unverified', 'delete_expired_otps']
    
    def mark_as_verified(self, request, queryset):
        """Mark selected OTPs as verified"""
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} OTP records were marked as verified.')
    mark_as_verified.short_description = "Mark selected as verified"
    
    def mark_as_unverified(self, request, queryset):
        """Mark selected OTPs as unverified"""
        count = queryset.update(is_verified=False)
        self.message_user(request, f'{count} OTP records were marked as unverified.')
    mark_as_unverified.short_description = "Mark selected as unverified"
    
    def delete_expired_otps(self, request, queryset):
        """Delete expired OTP records"""
        expired_otps = queryset.filter(expires_at__lt=timezone.now(), is_verified=False)
        count = expired_otps.count()
        expired_otps.delete()
        self.message_user(request, f'{count} expired OTP records were deleted.')
    delete_expired_otps.short_description = "Delete expired OTPs"


# Customize admin site headers
admin.site.site_header = "User Management Admin"
admin.site.site_title = "User Admin Portal"
admin.site.index_title = "Welcome to User Management Portal"