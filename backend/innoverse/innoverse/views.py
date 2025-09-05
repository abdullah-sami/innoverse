from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User
from rest_framework import viewsets, permissions, status, generics
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import *

from rest_framework.response import Response
from django.core.exceptions import PermissionDenied  
from django.shortcuts import redirect





class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        username = request.data.get('username')

        response = super().post(request, *args, **kwargs)

        # if response.status_code == status.HTTP_200_OK:
        #     self._process_successful_login(username, client_ip, user_agent, request)
        # else:
        #     self._process_failed_login(username, client_ip, user_agent, request)


        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    # def _process_successful_login(self, username, client_ip, user_agent, request):
    #     try:
    #         user = User.objects.get(username=username)

    #         logger.info(f"Successful login - User: {username} (ID: {user.id}), IP: {client_ip}")

    #         email_sent = send_login_email(username, 'success')

    #         if email_sent:
    #             logger.info(f"Login alert sent - User: {username}, Email: {user.email}")
    #         else:
    #             logger.warning(f"Failed to send login alert - User: {username}")

    #     except User.DoesNotExist:
    #         logger.error(f"User not found after authentication: {username}")
    #     except Exception as e:
    #         logger.error(f"Error processing login for {username}: {str(e)}")


    # def _process_failed_login(self, username, client_ip, user_agent, request):
    #     """Process successful login with enhanced logging"""
    #     try:
    #         user = User.objects.get(username=username)

    #         logger.info(f"Successful login - User: {username} (ID: {user.id}), IP: {client_ip}")

    #         email_sent = send_login_email(username, 'failed')

    #         if email_sent:
    #             logger.info(f"Login alert sent - User: {username}, Email: {user.email}")
    #         else:
    #             logger.warning(f"Failed to send login alert - User: {username}")

    #     except User.DoesNotExist:
    #         logger.error(f"User not found after authentication: {username}")
    #     except Exception as e:
    #         logger.error(f"Error processing login for {username}: {str(e)}")




def logout_view(request):
    logout(request)
    return redirect('login')

