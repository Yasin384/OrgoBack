# main/authentication.py

from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.utils import timezone
from datetime import timedelta
from rest_framework.authtoken.models import Token

# Настройка времени истечения токена (24 часа)
TOKEN_EXPIRATION_TIME = timedelta(hours=24)


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Кастомный класс аутентификации, который проверяет срок действия токена.
    Токен считается просроченным, если с момента его создания прошло более 24 часов.
    """

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.select_related('user').get(key=key)
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed('Токен не действителен.')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('Пользователь неактивен.')

        # Проверяем, не истек ли токен
        if timezone.now() > token.created + TOKEN_EXPIRATION_TIME:
            token.delete()  # Удаляем просроченный токен
            raise exceptions.AuthenticationFailed('Токен истек.')

        return (token.user, token)