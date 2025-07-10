from api.constants import INVALID_USERNAME
from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == INVALID_USERNAME:
        raise ValidationError(
            f'Недопустимое имя пользователя - {INVALID_USERNAME}.')
