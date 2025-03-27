from uuid import uuid4

import pytest
from flask import json
from unittest.mock import patch, MagicMock
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


##################################
# update_status endpoint Testing #
##################################
# update_status endpoint Testing'
# Test 1: Successful status update to 'active'
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_status_active_success(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    mock_cursor.fetchone.return_value = (VALID_UUID,)  # Simulate account found


    data = {
        "status": "active"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account status updated to active successfully"

# Test 2: Successful status update to 'disabled'
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_status_disabled_success(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    mock_cursor.fetchone.return_value = (VALID_UUID,)  # Simulate account found

    data = {
        "status": "disabled"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account status updated to disabled successfully"

# Test 3: Invalid status provided
@patch('app.auth.decorators.get_current_user')
def test_update_account_status_invalid_status(mock_get_current_user, client):
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    data = {
        "status": "unknown_status"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid status. Allowed values are 'active' or 'disabled'."

# Test 4: Account not found
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_status_account_not_found(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    mock_cursor.fetchone.return_value = None  # Simulate account not found

    data = {
        "status": "active"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"

# Test 5: Unexpected error during status update
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_update_account_status_unexpected_error(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    data = {
        "status": "active"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"
