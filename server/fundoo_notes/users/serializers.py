import re

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import Users


class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = Users
        fields = ['username', 'email', 'password']

        # extra_kwargs = {
        #     'password': {'write_only': True}  # Another way to make password write-only
        # }
        
    def validate_username(self, value):

        user_regex = r'^(?=.*[A-Z]).{3,}$'
        
        if not isinstance(value, str):
            raise serializers.ValidationError("Username must be a string")
        
        if not re.match(user_regex, value):
            raise serializers.ValidationError(
                "Username must be at least 3 characters long, include at least one uppercase letter, and one special character."
            )
        return value


    def validate_email(self, value):

        email_regex = r'^[a-z0-9._%+-]+@[a-z0-9]+\.[a-z]{2,}$'
        if not re.match(email_regex, value.lower()):
            raise serializers.ValidationError("Email must be a valid domain address")
        return value

    def validate_password(self, value):

        password_regex = r'^.{8,}$'
        
        if not re.match(password_regex, value):
            raise serializers.ValidationError("Password must be at least 8 characters long." )
        
        return value
    

    def create(self, validated_data):
        user=Users.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            
        )
        
        return user



class UserLoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):

        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)

        if not email or not password:
            raise serializers.ValidationError("Email and password required")
        
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            raise serializers.ValidationError({"message": "User with this email does not exist"})

        # Check if the password is correct
        if not user.check_password(password):
            raise serializers.ValidationError({"message": "Invalid password"})

        data['user'] = user
        return data
    
    
