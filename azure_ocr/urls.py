from django.urls import path
from .views import process_and_ocr  # Import the view

urlpatterns = [
    path('ocr/', process_and_ocr, name='ocr'),  # Keep the route as /ocr/
]
