from typing import Tuple
from email_validator import validate_email, EmailNotValidError
import re


class PasswordValidator:
    MIN_LENGTH = 8
    UPPERCASE_PATTERN = r'[A-Z]'
    LOWERCASE_PATTERN = r'[a-z]'
    NUMBER_PATTERN = r'[0-9]'
    SPECIAL_PATTERN = r'[!@#$%^&*(),.?":{}|<>]'

    @classmethod
    def validate(cls, password: str) -> Tuple[bool, str]:
        if not password:
            return False, "Password is required"

        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"

        if not re.search(cls.UPPERCASE_PATTERN, password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(cls.LOWERCASE_PATTERN, password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(cls.NUMBER_PATTERN, password):
            return False, "Password must contain at least one number"

        if not re.search(cls.SPECIAL_PATTERN, password):
            return False, "Password must contain at least one special character (!@#$%^&* etc.)"

        return True, "Password is valid"


class EmailValidator:
    @classmethod
    def is_valid_format(cls, email: str) -> bool:
        try:
            validate_email(email)  # raises on invalid
            return True
        except EmailNotValidError:
            return False
