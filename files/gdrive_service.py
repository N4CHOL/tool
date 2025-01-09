import os
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload,MediaIoBaseDownload
from googleapiclient.discovery import build
from django.conf import settings
def get_gdrive_service():
    # Use the path from settings.py directly
    credentials_path = str(settings.GOOGLE_API_CREDENTIALS)
    
    if not os.path.exists(credentials_path):
        raise ValueError(f"Credentials file not found at {credentials_path}")
    
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build('drive', 'v3', credentials=credentials)

def list_files(folder_id):
    service = get_gdrive_service()
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

def upload_file(file_path, file_name, folder_id):
    # Get the Google Drive service
    service = get_gdrive_service()
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    # Use resumable upload for larger files
    media = MediaFileUpload(file_path, resumable=True)
    
    try:
        # Attempt to upload the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')
    except Exception as e:
        print(f"Error uploading file {file_name} to folder {folder_id}: {e}")
        raise

def get_latest_file_id(folder_id=None):
    # If no folder_id is passed, use the default folder IDs from settings
    if folder_id is None:
        folder_id = settings.NEW_FILES_FOLDER_ID  # Or settings.NON_HANDWRITTEN_FOLDER_ID if needed
    

    # Get the Google Drive service
    service = get_gdrive_service()

    # Define the query to list files in the folder that are not trashed
    query = f"'{folder_id}' in parents and trashed=false"
    
    try:
        # List files in the folder and fetch relevant fields: id, name, and modifiedTime
        results = service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
        files = results.get('files', [])
        
        if not files:
            raise Exception("No files found in the specified folder.")

        # Sort the files by modifiedTime (descending order)
        latest_file = sorted(files, key=lambda x: x['modifiedTime'], reverse=True)[0]

        # Return the ID of the latest file
        return latest_file['id']
    
    except Exception as e:
        raise Exception(f"Error retrieving latest file ID: {str(e)}")

def download_file(file_id, destination_path):
    # Get the Google Drive service
    service = get_gdrive_service()

    try:
        # Get file metadata to extract the name
        file_metadata = service.files().get(fileId=file_id).execute()
        file_name = file_metadata.get('name')

        if not file_name:
            raise ValueError(f"File with ID {file_id} does not have a name.")

        # Request the file to be downloaded
        request = service.files().get_media(fileId=file_id)

        # Create a file handle for the destination
        fh = BytesIO()

        # Download the file in chunks and write to the file handle
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

        # Save the content to the local file
        with open(destination_path, 'wb') as f:
            fh.seek(0)  # Rewind the file handle to the beginning
            f.write(fh.read())

        print(f"File downloaded to {destination_path}.")
        return destination_path  # Return the path where the file is saved

    except Exception as e:
        print(f"Error downloading file with ID {file_id}: {e}")
        raise