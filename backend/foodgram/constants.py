from django.core.validators import RegexValidator

REGEX_COLOR = RegexValidator(r'^#[0-9A-F]{6}$', 'Поддерживаемые знаки.')

NAME_MAX_LENGTH = 150
TEXT_MAX_LENGTH = 200

DEFAULT_PAGES_LIMIT = 6
