# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import PosterTemplate, PackagePoster

@admin.register(PosterTemplate)
class PosterTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at', 'preview_image']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'preview_image']
    
    def preview_image(self, obj):
        if obj.background_image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.background_image.url
            )
        return "No Image"
    preview_image.short_description = "Preview"

@admin.register(PackagePoster)
class PackagePosterAdmin(admin.ModelAdmin):
    list_display = ['package_name', 'package_type', 'price', 'user', 'template', 'created_at', 'has_files']
    list_filter = ['package_type', 'template', 'created_at']
    search_fields = ['package_name', 'user__company_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'poster_previews']
    
    def has_files(self, obj):
        files = []
        if obj.poster_jpg:
            files.append('JPG')
        if obj.poster_png:
            files.append('PNG')
        if obj.poster_pdf:
            files.append('PDF')
        return ', '.join(files) if files else 'None'
    has_files.short_description = "Generated Files"
    
    def poster_previews(self, obj):
        previews = []
        if obj.poster_jpg:
            previews.append(format_html(
                '<div style="display: inline-block; margin: 5px;"><strong>JPG:</strong><br/>'
                '<img src="{}" width="150" height="200" style="object-fit: cover;" />'
                '<br/><a href="{}" target="_blank">Download</a></div>',
                obj.poster_jpg.url, obj.poster_jpg.url
            ))
        if obj.poster_png:
            previews.append(format_html(
                '<div style="display: inline-block; margin: 5px;"><strong>PNG:</strong><br/>'
                '<img src="{}" width="150" height="200" style="object-fit: cover;" />'
                '<br/><a href="{}" target="_blank">Download</a></div>',
                obj.poster_png.url, obj.poster_png.url
            ))
        if obj.poster_pdf:
            previews.append(format_html(
                '<div style="display: inline-block; margin: 5px;"><strong>PDF:</strong><br/>'
                '<a href="{}" target="_blank">Download PDF</a></div>',
                obj.poster_pdf.url
            ))
        
        return format_html(''.join(previews)) if previews else "No files generated"
    poster_previews.short_description = "Poster Previews"