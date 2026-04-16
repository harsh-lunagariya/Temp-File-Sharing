from rest_framework import serializers

from .models import FileUpload


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['file']


class DownloadSerializer(serializers.Serializer):
    key = serializers.RegexField(r'^\d{6}$', error_messages={'invalid': 'Enter a valid 6-digit key.'})


class FileUploadStatusSerializer(serializers.ModelSerializer):
    key = serializers.CharField(source='unique_key')
    filename = serializers.CharField(source='original_filename')
    status = serializers.CharField()

    class Meta:
        model = FileUpload
        fields = ['id', 'key', 'filename', 'status', 'uploaded_at', 'downloaded_at']
