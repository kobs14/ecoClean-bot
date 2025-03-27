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


#######################################
# get_account_status endpoint Testing #
#######################################

VALID_ACTIVE_ACCOUNT = {
    'account_id': '69b107b2-3ec2-4b21-be4e-4e4e85b28421',
    'account_username': 'active_user',
    'account_fullname': 'Active User',
    'account_status': 'active'
}

VALID_DISABLED_ACCOUNT = {
    'account_id': '47c907e2-4fc2-44a5-a839-fba4c91dd3bb',
    'account_username': 'disabled_user',
    'account_fullname': 'Disabled User',
    'account_status': 'disabled'
}

# Test 1: Successfully fetch active accounts
@patch('app.routes.account.routes.conn')
def test_get_accounts_by_status_active_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [VALID_ACTIVE_ACCOUNT]  # Simulate one active account found

    response = client.get('/account/accounts?status=active')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert len(result) == 1
    assert result[0]['account_status'] == 'active'
    assert result[0]['account_username'] == 'active_user'

# Test 2: Successfully fetch disabled accounts
@patch('app.routes.account.routes.conn')
def test_get_accounts_by_status_disabled_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [VALID_DISABLED_ACCOUNT]  # Simulate one disabled account found

    response = client.get('/account/accounts?status=disabled')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert len(result) == 1
    assert result[0]['account_status'] == 'disabled'
    assert result[0]['account_username'] == 'disabled_user'

# Test 3: Invalid status provided
def test_get_accounts_by_status_invalid_status(client):
    response = client.get('/account/accounts?status=invalid')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid status. Allowed values are 'active' or 'disabled'."

# Test 4: No accounts found for the given status
@patch('app.routes.account.routes.conn')
def test_get_accounts_by_status_no_accounts_found(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []  # Simulate no accounts found

    response = client.get('/account/accounts?status=active')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "No accounts found."

# Test 5: Unexpected error during fetching
@patch('app.routes.account.routes.conn')
def test_get_accounts_by_status_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.get('/account/accounts?status=active')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"