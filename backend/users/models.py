from api.constants import (AVATAR_UPLOAD_DIR, EMAIL_MAX_LENGTH,
                           NAME_MAX_LENGTH, USERNAME_MAX_LENGTH)
from django.contrib.auth.models import AbstractUser, UnicodeUsernameValidator
from django.db import models

from .validators import validate_username


class User(AbstractUser):
    """Модель пользователя."""
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH, unique=True, blank=False,
        validators=((UnicodeUsernameValidator(), validate_username)))
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH, unique=True, blank=False,
        verbose_name='email')
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH, blank=False, verbose_name='Имя')
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH, blank=False, verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to=AVATAR_UPLOAD_DIR, blank=True, verbose_name='Аватар',
        default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def get_number_of_recipes(self):
        return self.recipes.count()

    def get_number_of_subscribers(self):
        return self.subscribed_to.count()

    def __str__(self):
        return self.username
