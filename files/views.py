from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.conf import settings
from pathlib import Path
import os

from .gdrive_service import list_files, upload_file, download_file


class ListFilesView(APIView):
    permission_classes = [IsAuthenticated]  # Require JWT authentication

    def get(self, request):
        folder_id = request.query_params.get('folder_id')
        if not folder_id:
            return Response({"error": "Folder ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            files = list_files(folder_id)
            return Response({"files": files}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UploadFileView(APIView):
    permission_classes = [IsAuthenticated]  # Require JWT authentication

    def post(self, request):
        folder_id = request.data.get('folder_id')
        file_name = request.data.get('file_name')
        file = request.FILES.get('file')

        if not folder_id or not file_name or not file:
            return Response({"error": "Folder ID, file name, and file are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert MEDIA_ROOT to a Path object and ensure file path is correct
            media_path = Path(settings.MEDIA_ROOT) / file_name

            # Save the file to MEDIA_ROOT (project's media folder)
            with default_storage.open(media_path, 'wb') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            # Now upload to Google Drive
            file_id = upload_file(media_path, file_name, folder_id)

            # Optionally remove the file from the local filesystem after upload
            os.remove(media_path)

            return Response({"file_id": file_id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadFileView(APIView):
    permission_classes = [IsAuthenticated]  # Require JWT authentication

    def get(self, request):
        folder_id = request.query_params.get('folder_id')
        if not folder_id:
            return Response({"error": "Folder ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # List files in the folder
            files = list_files(folder_id)

            # Ensure there are files in the folder
            if not files:
                return Response({"error": "No files found in the folder"}, status=status.HTTP_404_NOT_FOUND)

            # Get the last uploaded file (you may need a more specific logic here)
            last_uploaded_file = files[-1]
            file_id = last_uploaded_file['id']
            file_name = last_uploaded_file['name']

            # Define the path to download the file locally
            download_path = Path(settings.MEDIA_ROOT) / file_name

            # Download the file from Google Drive
            download_file(file_id, download_path)

            return Response({"message": f"File downloaded successfully to {download_path}"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
