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


################################
# update_account endpoint tests#
################################

# Test 1: Update account success
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_success(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.rowcount = 1  # Simulate successful update
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }

    data = {
        "username": "new_username",
        "phone": "1234567890"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account updated successfully"

# Test 2: Invalid UUID format
@patch('app.auth.decorators.get_current_user')
def test_update_account_invalid_uuid(mock_get_current_user, client):
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    data = {
        "username": "new_username"
    }
    response = client.patch(f'/account/{INVALID_UUID}', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format"

# Test 3: No valid fields to update
@patch('app.auth.decorators.get_current_user')
def test_update_account_no_fields(mock_get_current_user, client):
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }

    data = {}  # Empty body, no fields to update

    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "No valid fields to update"

# Test 4: Account not found
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_not_found(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.rowcount = 0  # Simulate account not found
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }

    data = {
        "username": "new_username"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"

# Test 5: Unique violation on username
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_username_exists(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation("duplicate key value violates unique constraint \"account_username_key\"")
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }

    data = {
        "username": "existing_username"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Username already exists."

# Test 6: Unique violation on phone number
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_phone_exists(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation("duplicate key value violates unique constraint \"account_phone_key\"")
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }

    data = {
        "phone": "1234567890"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Phone number already exists."

# Test 7: Unexpected error during update
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_unexpected_error(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    data = {
        "username": "new_username"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"