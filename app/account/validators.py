import re
from email_validator import validate_email, EmailNotValidError

from app.config import logger
from decimal import Decimal, InvalidOperation


def validate_email_address(email):
    """
    Validate the email format.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email format is valid, False otherwise.
    """
    try:
        # Validate the email address and return the normalized version
        valid = validate_email(email)  # Will raise EmailNotValidError if the email is invalid
        return True
    except EmailNotValidError as e:
        # Email not valid.
        logger.warning(f"Invalid email address '{email}': {str(e)}")
        return False

def is_valid_phone(phone):
    """Validate phone number format."""
    return re.match(r'^\+?[\d\s-]+$', phone) is not None



def validate_field(field_name, value):
    """Validate individual fields with specific logic."""
    if field_name == 'account_is_admin':
        # Validate account_is_admin format
        if not isinstance(value, bool):
            raise ValueError("account_is_admin must be a boolean")
        return value
    if field_name == 'account_commission_rate':
        # Validate account_commission_rate format
        try:
            rate = Decimal(value)
            if rate < 0 or rate > 100:
                raise ValueError("Commission rate must be between 0 and 100")
            return rate
        except InvalidOperation:
            raise ValueError("Invalid commission rate format")
    elif field_name == 'account_status':
        # Validate account status format
        if value not in ['active', 'disabled']:
            raise ValueError("Invalid account status")
        return value
    elif field_name == 'account_phone':
        # Validate phone number format
        if not re.match(r'^\+?[\d\s-]+$', value):
            raise ValueError("Invalid phone number format.")
        return value
    elif field_name == 'account_username':
        # Validate username format
        if not isinstance(value, str) or len(value) < 3 or len(value) > 50:
            raise ValueError("Username must be a string between 3 and 50 characters")
        return value
    elif field_name == 'account_fullname':
        # Validate full name format
        if not isinstance(value, str) or len(value) < 2 or len(value) > 100:
            raise ValueError("Full name must be a string between 2 and 100 characters")
        if not all(part.isalpha() or part.isspace() for part in value):
            raise ValueError("Full name must contain only letters and spaces")
        return value
    elif field_name == 'account_password_hash':
        # Validate password
        if not isinstance(value, str) or len(value) < 8:
            raise ValueError("Password must be a string of at least 8 characters")
        # if not re.search(r'[A-Z]', value):
        #     raise ValueError("Password must contain at least one uppercase letter")
        # if not re.search(r'[a-z]', value):
        #     raise ValueError("Password must contain at least one lowercase letter")
        # if not re.search(r'\d', value):
        #     raise ValueError("Password must contain at least one digit")
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        #     raise ValueError("Password must contain at least one special character")
        return value
    else:
        raise ValueError(f"Unknown field: {field_name}")