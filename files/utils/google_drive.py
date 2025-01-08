# files/utils/google_drive.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    """Authenticate and return the Google Drive service client."""
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_API_CREDENTIALS'),
        scopes=SCOPES
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service
