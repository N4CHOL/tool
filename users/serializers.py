from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def create(self, validated_data):
        """
        Create and return a new user, with the password hashed.
        """
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Hash password
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Update and return an existing user, with password hashing if provided.
        """
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)  # Hash new password if provided

        instance.save()
        return instance
