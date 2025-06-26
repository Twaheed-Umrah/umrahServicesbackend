
from django.contrib import admin
from django.utils.html import format_html
from .models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'package_type', 
        'destination', 
        'duration_days', 
        'formatted_price', 
        'formatted_discount_price',
        'is_active', 
        'created_by', 
        'assigned_to',
        'created_at'
    ]
    
    list_filter = [
        'package_type',
        'is_active',
        'created_by',
        'assigned_to',
        'destination',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'description',
        'destination',
        'created_by__username',
        'created_by__email',
        'assigned_to__username',
        'assigned_to__email'
    ]
    
    list_editable = ['is_active']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Package Information', {
            'fields': ('name', 'description', 'package_type', 'destination', 'duration_days', 'image')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price')
        }),
        ('Assignment & Status', {
            'fields': ('created_by', 'assigned_to', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom methods for better display
    def formatted_price(self, obj):
        return f"${obj.price:,.2f}"
    formatted_price.short_description = 'Price'
    formatted_price.admin_order_field = 'price'
    
    def formatted_discount_price(self, obj):
        if obj.discount_price:
            return f"${obj.discount_price:,.2f}"
        return "-"
    formatted_discount_price.short_description = 'Discount Price'
    formatted_discount_price.admin_order_field = 'discount_price'
    
    # Customize the queryset to optimize database queries
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by', 'assigned_to')
    
    # Set default values for new packages
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new package
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Customize the form for better UX
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "created_by":
            kwargs["queryset"] = db_field.related_model.objects.filter(is_staff=True)
        elif db_field.name == "assigned_to":
            # You might want to filter this based on user roles
            kwargs["queryset"] = db_field.related_model.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    # Add custom actions
    actions = ['activate_packages', 'deactivate_packages']
    
    def activate_packages(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} packages were successfully activated.')
    activate_packages.short_description = "Activate selected packages"
    
    def deactivate_packages(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} packages were successfully deactivated.')
    deactivate_packages.short_description = "Deactivate selected packages"