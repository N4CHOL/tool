from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from .serializers import LoginSerializer

class LoginView(APIView):
    # Allow unauthenticated access
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="User login.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response("Login successful", LoginSerializer),
            400: openapi.Response("Bad request", openapi.Schema(type=openapi.TYPE_OBJECT)),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Return validated data on successful login
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        # Return errors if validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
