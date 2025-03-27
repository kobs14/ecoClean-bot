import pytest
from flask import json
from unittest.mock import patch, MagicMock
from app.main import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()


###################################
# delete_account endpoint Testing #
###################################

# Test for successful deletion of an account
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_delete_account_success(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'account_id': '123e4567-e89b-12d3-a456-426614174000'}
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }

    response = client.delete('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account and associated records deleted successfully"
    mock_cursor.execute.assert_called()


# Test for invalid account ID format
@patch('app.auth.decorators.get_current_user')
def test_delete_account_invalid_id_format(mock_get_current_user, client):
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    response = client.delete('/account/invalid-id')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format"


# Test for account not found

@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_delete_account_not_found(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    mock_cursor.fetchone.return_value = None  # Simulate no account found

    response = client.delete('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"


# Test for unexpected error during deletion
@patch('app.routes.account.routes.conn')
@patch('app.auth.decorators.get_current_user')
def test_delete_account_unexpected_error(mock_get_current_user, mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_current_user.return_value = {
        "account_id": "123e4567-e89b-12d3-a456-426614174000",
        "account_is_admin": True  # Ensure the user is an admin
    }
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.delete('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An unexpected error occurred while deleting the account."

