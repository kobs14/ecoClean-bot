from uuid import uuid4

import psycopg2
import pytest
from flask import json
from unittest.mock import patch, MagicMock, ANY
from app.main import create_app

# Sample UUIDs for testing
VALID_UUID = str(uuid4())
INVALID_UUID = 'invalid-uuid'

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()


# Test for successful account creation
@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')
def test_create_account_success(mock_send_email, mock_get_current_user, mock_conn, client):
    # Step 1: Mock user authentication
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Step 2: Mock database operations
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"account_id": "987e4567-e89b-12d3-a456-426614174111"}

    # Mocked request payload
    mock_data = {
        "username": "testuser",
        "fullname": "Test User",
        "phone": "1234567890",
        "password": "securepassword",
        "email": "test@gmail.com"
    }

    # Step 3: Send request and validate response
    response = client.post('/account/register', json=mock_data)
    assert response.status_code == 201
    assert "Account, email, and Telegram entry created successfully" in response.json["message"]

    # Ensure send_email was called with expected arguments
    mock_send_email.assert_called_once_with(
        to_email="test@gmail.com",
        subject="Welcome to Our Service",
        body=ANY
    )


# Test for missing required fields
@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_create_account_missing_required_fields(mock_get_current_user, mock_conn, client):
    # Mock the get_current_user function to return a valid admin user
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Test data with missing required fields
    data = {
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Missing required field: username"


@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_create_account_non_admin(mock_get_current_user, mock_conn, client):
    # Mock the get_current_user function to return a non-admin user
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": False  # Non-admin user
    }

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'is_admin': True,
        'commission_rate': 0.10,
        'status': 'active'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 403
    result = json.loads(response.data)
    assert result['message'] == "Forbidden: Admin access required"



@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_create_account_unauthenticated(mock_get_current_user, mock_conn, client):
    # Mock the get_current_user function to return None (unauthenticated user)
    mock_get_current_user.return_value = None

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'is_admin': True,
        'commission_rate': 0.10,
        'status': 'active'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 401
    result = json.loads(response.data)
    assert result['message'] == "Unauthorized: Invalid or missing account_id"



# Test for invalid phone format
@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_create_account_invalid_phone(mock_get_current_user,mock_conn, client):

    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    # Test data with invalid phone format
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': 'invalid_phone',
        'password': 'testpassword'
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid phone number format."


# Test for username already exists (DB error)
@patch('app.account.routes.conn')  # Mock database connection
@patch('app.auth.decorators.get_current_user')  # Mock authentication
@patch('app.mail.mail.send_email')  # Mock email sending
def test_create_account_username_exists(mock_send_email, mock_get_current_user, mock_conn, client):
    """Test that attempting to register with an existing username returns 409 Conflict."""

    mock_send_email.return_value = None

    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation(
        "duplicate key value violates unique constraint \"account_username_key\""
    )

    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    data = {
        "username": "existinguser",
        "fullname": "Test User",
        "phone": "1234567890",
        "password": "testpassword",
        "email": "existinguser@gmail.com"  # Ensure this exists
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 409, f"Expected 409 but got {response.status_code}"

    result = json.loads(response.data)
    assert result["message"] == "Username already exists.", f"Unexpected message: {result}"



# Test for phone number already exists (DB error)
@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_create_account_phone_exists(mock_get_current_user, mock_conn, client):
    # Step 1: Mock cursor behavior to simulate a UniqueViolation error for phone number
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor


    # Simulate the UniqueViolation error when the phone number already exists
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation(
        "duplicate key value violates unique constraint \"account_phone_key\"")

    # Step 2: Mock current user (ensure they are an admin)
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Step 3: Define test data with a phone number that already exists
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',  # Phone number already exists in DB
        'password': 'testpassword',
        "email": "existinguser@gmail.com"
    }

    # Step 4: Send the POST request to register the account
    response = client.post('/account/register', json=data)

    # Step 5: Validate the response
    assert response.status_code == 409  # Conflict status for duplicate entry
    result = json.loads(response.data)
    assert result['message'] == "Phone number already exists."  # Expected error message



# Test for optional fields being passed
@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')  # Mock email sending
def test_create_account_with_optional_fields(mock_send_email, mock_get_current_user, mock_conn, client):
    # Step 1: Mock cursor behavior to simulate successful account creation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_send_email.return_value = True

    # Simulate account ID retrieval after account creation
    mock_cursor.fetchone.return_value = {'account_id': 1}

    # Step 2: Mock current user (ensure they are an admin)
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Step 3: Define test data with both required and optional fields
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'is_admin': True,
        'commission_rate': 0.05,  # Optional field
        'status': 'active' , # Optional field
        'email': 'existinguser@gmail.com'
    }

    # Step 4: Send the POST request to register the account
    response = client.post('/account/register', json=data)

    # Step 5: Validate the response
    assert response.status_code == 201  # Created status for successful account creation
    result = json.loads(response.data)
    assert result['message'] == "Account, email, and Telegram entry created successfully"  # Expected success message



@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')  # Mock email sending
def test_create_account_duplicate_email(mock_send_email, mock_get_current_user, mock_conn, client):
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Mock cursor behavior for duplicate email error
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation("Duplicate email")

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'email': 'test@gmail.com',  # Duplicate email
        'is_admin': True,
        'commission_rate': 0.10,
        'status': 'active'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Email already exists."


@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')
def test_create_account_email_failure(mock_send_email, mock_get_current_user, mock_conn, client):
    # Mock the get_current_user function to return a valid admin user
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Mock cursor behavior for successful account creation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'account_id': '123e4567-e89b-12d3-a456-426614174000'}

    # Mock the send_email function to return False (failure)
    mock_send_email.return_value = False

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'email': 'john.doe@gmail.com',
        'is_admin': True,
        'commission_rate': 0.10,
        'status': 'active'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Failed to send welcome email"


# Test for handling unexpected errors
@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')
def test_create_account_unexpected_error(mock_send_email, mock_get_current_user, mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'email': 'example@gmail.com'
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"



@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')
def test_create_account_duplicate_verification_token(mock_send_email, mock_get_current_user, mock_conn, client):
    # Mock the get_current_user function to return a valid admin user
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Mock cursor behavior to simulate a UniqueViolation error for the verification token
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation(
        "duplicate key value violates unique constraint \"telegram_verification_token_key\""
    )

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'email': 'testuser@gmail.com',
        'is_admin': True,
        'commission_rate': 0.10,
        'status': 'active'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 500
    result = json.loads(response.data)
    assert "An unexpected error occurred" in result['error']

@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')
def test_create_account_foreign_key_violation(mock_send_email, mock_get_current_user, mock_conn, client):
    # Mock the get_current_user function to return a valid admin user
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Mock cursor behavior to simulate a ForeignKeyViolation error
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.ForeignKeyViolation(
        "insert or update on table \"telegram\" violates foreign key constraint \"telegram_account_id_fkey\""
    )

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'email': 'testuser@gmail.com',
        'is_admin': True,
        'commission_rate': 0.10,
        'status': 'active'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 500



@patch('app.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
@patch('app.account.routes.send_email')
def test_create_account_invalid_email(mock_send_email, mock_get_current_user, mock_conn, client):
    # Mock the get_current_user function to return a valid admin user
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True
    }

    # Test data with an invalid email
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'email': 'invalid-email',  # Invalid email format
        'is_admin': True,
        'commission_rate': 0.10,
        'status': 'active'
    }

    # Make the request
    response = client.post('/account/register', json=data)

    # Assert the response
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid email address"
