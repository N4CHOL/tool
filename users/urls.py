from django.urls import path
from .views import UsersListView, UserDetailView

urlpatterns = [
    # List users or create a new user
    path('users/', UsersListView.as_view(), name='user-list'),  # GET for all users, POST to create a user
    
    # Retrieve, update, or delete a user by ID
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),  # GET, PUT, DELETE for a specific user
]
