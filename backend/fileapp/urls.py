from django.urls import path

from .views import DownloadFileView, FileListView, UploadFileView


urlpatterns = [
    path('upload/', UploadFileView.as_view(), name='upload-file'),
    path('download/', DownloadFileView.as_view(), name='download-file'),
    path('files/', FileListView.as_view(), name='list-files'),
]
