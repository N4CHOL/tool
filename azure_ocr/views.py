import os
import requests
import time
from django.conf import settings
from django.http import JsonResponse
from files.gdrive_service import download_file, get_latest_file_id, get_gdrive_service, upload_file  # Assuming this function works
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Azure OCR API Endpoint and Keys
AZURE_OCR_API_URL = "https://cv-app-002.cognitiveservices.azure.com/vision/v3.2/read/analyze"
OCR_API_KEY = settings.VITE_OCR_APP_PREDICTION_KEY
def poll_for_result(operation_location):
    headers = {
        'Ocp-Apim-Subscription-Key': OCR_API_KEY,
    }

    # Poll every 2 seconds until the status is "succeeded"
    while True:
        poll_response = requests.get(operation_location, headers=headers)
        result = poll_response.json()
        
        if poll_response.status_code != 200:
            return {"error": "Failed to get the status of OCR", "status_code": poll_response.status_code}
        
        status = result.get('status')
        if status == 'succeeded':
            return result  # Return the successful result
        elif status == 'failed':
            return {"error": "OCR processing failed"}
        
        # Wait before polling again (poll every 2 seconds)
        time.sleep(2)

def send_to_azure_ocr(file_path):
    with open(file_path, 'rb') as file:
        headers = {
            'Ocp-Apim-Subscription-Key': OCR_API_KEY,  # Correct header for Azure OCR
            'Content-Type': 'application/octet-stream',  # Content type to handle various file types
        }
        response = requests.post(AZURE_OCR_API_URL, headers=headers, data=file)
        
        if response.status_code == 202:
            # The request has been accepted, now poll for the result
            operation_location = response.headers.get('Operation-Location')
            if operation_location:
                return poll_for_result(operation_location)
            else:
                return {"error": "Operation location not found"}
        else:
            return {"error": "Failed to get a response from Azure OCR", "status_code": response.status_code, "message": response.text}
@swagger_auto_schema(
    operation_description="Process a file through Azure OCR and upload it to Google Drive.",
    manual_parameters=[
        openapi.Parameter('folder_id', openapi.IN_QUERY, description="Google Drive Folder ID", type=openapi.TYPE_STRING)
    ],
    responses={
        200: openapi.Response(
            description="Successfully processed and uploaded the file.",
            examples={
                "application/json": {
                    "ocr_response": {},  # Replace with a valid example
                    "contains_handwritten_text": 0,
                    "uploaded_file_id": "file_id"
                }
            }
        ),
        400: openapi.Response(description="Bad request. Folder ID is missing or invalid."),
        500: openapi.Response(description="Internal server error. File processing or upload failed.")
    }
)
def process_and_ocr(request):
    folder_id = request.GET.get('folder_id')
    
    if not folder_id:
        return JsonResponse({"error": "Folder ID is required"}, status=400)

    # Step 1: Get the latest file ID from Google Drive
    try:
        file_id = get_latest_file_id(folder_id)  # Get the latest file ID
    except Exception as e:
        return JsonResponse({"error": f"Error retrieving file ID: {str(e)}"}, status=500)

    # Step 2: Download the file from Google Drive and get its metadata
    try:
        # Fetch file metadata, which includes file name and extension
        service = get_gdrive_service()
        file_metadata = service.files().get(fileId=file_id).execute()
        file_name = file_metadata['name']

        # Define the destination path using the correct file name (with extension)
        destination_path = os.path.join(settings.MEDIA_ROOT, file_name)

        # Step 3: Download the file to the correct location with its original extension
        download_file(file_id, destination_path)  # Pass the file path to download the file

        # Verify the file has been downloaded successfully
        if not os.path.exists(destination_path):
            return JsonResponse({"error": f"Downloaded file not found at {destination_path}"}, status=500)

    except Exception as e:
        return JsonResponse({"error": f"Error downloading file: {str(e)}"}, status=500)

 # Step 4: Send the downloaded file to Azure OCR API
    try:
        ocr_response = send_to_azure_ocr(destination_path)
    except Exception as e:
        return JsonResponse({"error": f"Error during OCR processing: {str(e)}"}, status=500)

    # Step 5: Check the OCR response for handwritten text
    try:
        # Azure OCR response typically includes "readResults" containing the analysis
        read_results = ocr_response.get('analyzeResult', {}).get('readResults', [])
        contains_handwritten_text = 0  # Default to 0 (no handwritten text)

        for page in read_results:
            for line in page.get('lines', []):
                # Check if the line or word has handwritten text
                if line.get('appearance', {}).get('style', {}).get('name') == 'handwriting':
                    contains_handwritten_text = 1  # Set to 1 if handwriting is detected
                    break
            if contains_handwritten_text == 1:
                break

    except Exception as e:
        return JsonResponse({"error": f"Error checking OCR response for handwritten text: {str(e)}"}, status=500)

    # Step 6: Upload the file to the appropriate Google Drive folder
    try:
        # Retrieve the folder IDs from environment variablesif folder_id is None:
        handwritten_folder_id = settings.HANDWRITTEN_FOLDER_ID
        non_handwritten_folder_id = settings.NON_HANDWRITTEN_FOLDER_ID


        if not handwritten_folder_id or not non_handwritten_folder_id:
            return JsonResponse({"error": "Target folder IDs are not set in environment variables"}, status=400)

        # Choose the target folder based on whether handwriting is detected
        target_folder_id = handwritten_folder_id if contains_handwritten_text == 1 else non_handwritten_folder_id

        # Upload the file to Google Drive
        uploaded_file_id = upload_file(destination_path, file_name, target_folder_id)

        # Delete the file from the temp folder after uploading
        os.remove(destination_path)

        return JsonResponse({
            "ocr_response": ocr_response,
            "contains_handwritten_text": contains_handwritten_text,
            "uploaded_file_id": uploaded_file_id
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": f"Error uploading file to Google Drive: {str(e)}"}, status=500)

