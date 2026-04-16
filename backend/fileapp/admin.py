from django.contrib import admin
from .models import FileUpload


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ('unique_key', 'original_filename', 'status', 'uploaded_at', 'downloaded_at')
    list_filter = ('is_downloaded', 'uploaded_at')
    search_fields = ('unique_key', 'file')
