from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from thesis.models import Coordinator
import logging

logger = logging.getLogger('custom_auth')

class CustomAdminBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.info(f"Attempting to authenticate user: {username}")
        user = super().authenticate(request, username, password, **kwargs)
        if user:
            if Coordinator.objects.filter(user=user).exists():
                logger.info(f"User {username} authenticated successfully as coordinator.")
                return user
            else:
                logger.warning(f"User {username} is not a coordinator.")
        else:
            logger.warning(f"Authentication failed for user: {username}")
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
