from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

# urlpatterns = [
#     path("register/",register_user,name="register_user"),
#     path("login/",login_user,name="login_user")
# ]
from .views import *

# from .views import register_user,login_user


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),

    path('verify/<str:token>/', verify_registered_user, name='verify_registered_user')
]