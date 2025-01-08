from django.urls import path
from .views import ListFilesView, UploadFileView, DownloadFileView

urlpatterns = [
    path('list-files/', ListFilesView.as_view(), name='list-files'),
    path('upload-file/', UploadFileView.as_view(), name='upload-file'),
    path('download-file/', DownloadFileView.as_view(), name='upload-file'),
]
