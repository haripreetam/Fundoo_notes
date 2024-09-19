from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Users
from .serializers import UserLoginSerializer, UserRegistrationSerializer


@api_view(['GET'])
def verify_registered_user(request, token: str):
    
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = decoded_token.get("user_id")
        user = Users.objects.get(id=user_id)

        if user.is_verified:
            return Response({
                'message': 'User is already verified',
                'status': 'success'
            }, status=status.HTTP_200_OK)

        user.is_verified = True
        user.save()

        return Response({
            'message': 'User verified successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except ExpiredSignatureError:
        return Response({
            'message': 'Verification link has expired',
            'status': 'error',
        }, status=status.HTTP_400_BAD_REQUEST)

    except InvalidTokenError:
        return Response({
            'message': 'Invalid verification link',
            'status': 'error',
        }, status=status.HTTP_400_BAD_REQUEST)

    except Users.DoesNotExist:
        return Response({
            'message': 'User not found',
            'status': 'error',
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            'message': 'An unexpected error occurred during verification',
            'status': 'error',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterUserView(APIView):
    authentication_classes = []
    permission_classes = []
    @csrf_exempt
    def post(self, request):
    
        try:
            serializer = UserRegistrationSerializer(data=request.data)
    
            if serializer.is_valid():
                user = serializer.save()

                # Generate JWT token
                payload = {
                    'user_id': user.id,
                    'exp': datetime.now(tz=timezone.utc)+ timedelta(hours=24),
                    'iat': datetime.now(tz=timezone.utc)
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

                # Create verification URL with token
                # verification_url = f"http://127.0.0.1:8000/users/verify/{token}/"
                verification_url = request.build_absolute_uri(
                        reverse('verify_registered_user', args=[token])
                    )
                
                # Send email with verification token
                send_mail(
                    'Verify Your Email',
                    f'Click the link to verify your email: {verification_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                return Response({
                    "message": "User registered successfully",
                    "status": "success",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            
            else:
                return Response({
                    "message": "Validation error",
                    "status": "error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:

            return Response({
                "message": "An unexpected error occurred",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class LoginUserView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                
                # generate JWT Token manually.
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "User logged in successfully",
                    "status": "success",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }, status=status.HTTP_200_OK)
            
            return Response({
                "message": "Validation error",
                "status": "error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "message": "An unexpected error occurred",
                "status": "error",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)