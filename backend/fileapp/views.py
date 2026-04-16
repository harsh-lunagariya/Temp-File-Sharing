import mimetypes
from pathlib import Path

from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FileUpload
from .serializers import DownloadSerializer, FileUploadSerializer, FileUploadStatusSerializer


class UploadFileView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        FileUpload.cleanup_expired()
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.save()
        return Response({'key': upload.unique_key}, status=status.HTTP_201_CREATED)


class DownloadFileView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        FileUpload.cleanup_expired()
        serializer = DownloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key = serializer.validated_data['key']
        try:
            upload = FileUpload.objects.get(unique_key=key, is_downloaded=False)
        except FileUpload.DoesNotExist:
            return Response({'detail': 'Invalid or expired key.'}, status=status.HTTP_404_NOT_FOUND)

        file_path = Path(upload.file.path)
        if not file_path.exists():
            upload.delete()
            return Response({'detail': 'Invalid or expired key.'}, status=status.HTTP_404_NOT_FOUND)

        file_bytes = file_path.read_bytes()
        upload.schedule_file_deletion()
        upload.delete()
        content_type = mimetypes.guess_type(upload.original_filename)[0] or 'application/octet-stream'
        response = HttpResponse(file_bytes, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{upload.original_filename}"'
        return response


class FileListView(APIView):
    def get(self, request):
        FileUpload.cleanup_expired()
        requested_keys = request.query_params.get('keys', '')
        keys = [key.strip() for key in requested_keys.split(',') if key.strip()]
        queryset = FileUpload.objects.none() if not keys else FileUpload.objects.filter(unique_key__in=keys).order_by('-uploaded_at')
        serializer = FileUploadStatusSerializer(queryset, many=True)
        return Response(serializer.data)
