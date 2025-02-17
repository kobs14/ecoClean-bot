import pytest
from app.account.validators import validate_email_address, is_valid_phone, validate_field


# Test for validate_email_address function
def test_validate_email_address_valid():
    assert validate_email_address("test@gmail.com") is True

def test_validate_email_address_invalid():
    assert validate_email_address("invalid-email") is False

# Test for is_valid_phone function
def test_is_valid_phone_valid():
    assert is_valid_phone("+1234567890") is True
    assert is_valid_phone("123-456-7890") is True
    assert is_valid_phone("1234567890") is True

def test_is_valid_phone_invalid():
    assert is_valid_phone("invalid-phone") is False
    assert is_valid_phone("12345abc") is False

# Test for validate_field function
def test_validate_field_account_is_admin():
    assert validate_field('account_is_admin', True) is True
    assert validate_field('account_is_admin', False) is False
    with pytest.raises(ValueError):
        validate_field('account_is_admin', "not a boolean")

def test_validate_field_account_commission_rate():
    assert validate_field('account_commission_rate', 50) == 50
    assert validate_field('account_commission_rate', 0) == 0
    assert validate_field('account_commission_rate', 100) == 100
    with pytest.raises(ValueError):
        validate_field('account_commission_rate', 150)  # out of range
    with pytest.raises(ValueError):
        validate_field('account_commission_rate', -10)  # out of range
    with pytest.raises(ValueError):
        validate_field('account_commission_rate', "invalid")  # invalid type

def test_validate_field_account_status():
    assert validate_field('account_status', 'active') == 'active'
    assert validate_field('account_status', 'disabled') == 'disabled'
    with pytest.raises(ValueError):
        validate_field('account_status', 'unknown')  # invalid status

def test_validate_field_account_phone():
    assert validate_field('account_phone', '+123-456-7890') == '+123-456-7890'
    assert validate_field('account_phone', '1234567890') == '1234567890'
    with pytest.raises(ValueError):
        validate_field('account_phone', 'invalid-phone')  # invalid phone format

def test_validate_field_account_username():
    assert validate_field('account_username', 'user123') == 'user123'
    with pytest.raises(ValueError):
        validate_field('account_username', 'ab')  # too short
    with pytest.raises(ValueError):
        validate_field('account_username', 'a' * 51)  # too long
    with pytest.raises(ValueError):
        validate_field('account_username', 123)  # invalid type

def test_validate_field_account_fullname():
    assert validate_field('account_fullname', 'John Doe') == 'John Doe'
    with pytest.raises(ValueError):
        validate_field('account_fullname', 'A')  # too short
    with pytest.raises(ValueError):
        validate_field('account_fullname', 'A' * 101)  # too long
    with pytest.raises(ValueError):
        validate_field('account_fullname', 'John123')  # invalid characters

def test_validate_field_account_password_hash():
    assert validate_field('account_password_hash', 'securepassword') == 'securepassword'
    with pytest.raises(ValueError):
        validate_field('account_password_hash', 'short')  # too short
