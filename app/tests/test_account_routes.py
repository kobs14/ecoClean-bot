from uuid import UUID, uuid4

import psycopg2
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


def test_test_route(client):
    response = client.get('/account/test')
    assert response.status_code == 200
    assert response.data == b"Test route is working"


def test_list_routes(client):
    response = client.get('/account/routes')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(isinstance(route, dict) for route in data)


@patch('app.account.routes.conn')
def test_db_test_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'1': 1}

    response = client.get('/account/db-test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Database connection successful"
    assert data['result'] == {'1': 1}


@patch('app.account.routes.conn')
def test_db_test_failure(mock_conn, client):
    mock_conn.cursor.side_effect = Exception("DB Error")

    response = client.get('/account/db-test')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['message'] == "Database connection failed"
    assert "DB Error" in data['error']


# Test for successful account creation
@patch('app.account.routes.conn')
def test_create_account_success(mock_conn, client):
    # Mock cursor behavior for successful account creation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'account_id': 1}

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

    response = client.post('/account/register', json=data)

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['message'] == "Account created successfully"


# Test for missing required fields
@patch('app.account.routes.conn')
def test_create_account_missing_fields(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Missing the 'username' field
    data = {
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword'
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Missing required field: username"


# Test for invalid phone format
@patch('app.account.routes.conn')
def test_create_account_invalid_phone(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

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
@patch('app.account.routes.conn')
def test_create_account_username_exists(mock_conn, client):
    # Mock cursor behavior to simulate a UniqueViolation error for username
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation(
        "duplicate key value violates unique constraint \"account_username_key\"")

    # Test data with a username that already exists
    data = {
        'username': 'existinguser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword'
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Username already exists."


# Test for phone number already exists (DB error)
@patch('app.account.routes.conn')
def test_create_account_phone_exists(mock_conn, client):
    # Mock cursor behavior to simulate a UniqueViolation error for phone number
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation(
        "duplicate key value violates unique constraint \"account_phone_key\"")

    # Test data with a phone number that already exists
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',  # Phone number already exists in DB
        'password': 'testpassword'
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Phone number already exists."


# Test for optional fields being passed
@patch('app.account.routes.conn')
def test_create_account_with_optional_fields(mock_conn, client):
    # Mock cursor behavior for successful account creation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'account_id': 1}

    # Test data with optional fields
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword',
        'is_admin': True,
        'commission_rate': 0.05,  # Optional field
        'status': 'active'  # Optional field
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['message'] == "Account created successfully"


# Test for handling unexpected errors
@patch('app.account.routes.conn')
def test_create_account_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    # Test data
    data = {
        'username': 'testuser',
        'fullname': 'Test User',
        'phone': '1234567890',
        'password': 'testpassword'
    }

    response = client.post('/account/register', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"


#############################
# get_account endpoint tests#
#############################

@patch('app.account.routes.conn')
def test_get_account_success(mock_conn, client):
    # Mock the database cursor and its return values
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    account_id = "123e4567-e89b-12d3-a456-426614174000"
    account_data = {
        "account_id": account_id,
        "account_username": "testuser",
        "account_fullname": "Test User",
        "account_phone": "1234567890",
        "account_is_admin": False,
        "account_commission_rate": 0.1,
        "account_status": "active"
    }
    email_data = [
        {"email_id": 1, "email_address": "test@example.com"}
    ]
    telegram_data = {
        "telegram_id": 1,
        "telegram_username": "testuser",
        "telegram_chat_id": "12345"
    }

    # Set up the mock cursor to return appropriate data for each query
    mock_cursor.fetchone.side_effect = [account_data, telegram_data]
    mock_cursor.fetchall.return_value = email_data

    response = client.get(f'/account/{account_id}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["account_id"] == account_id
    assert "emails" in result
    assert "telegram" in result


@patch('app.account.routes.conn')
def test_get_account_invalid_uuid(mock_conn, client):
    response = client.get('/account/invalid-uuid')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format"


@patch('app.account.routes.conn')
def test_get_account_not_found(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Simulate account not found

    response = client.get('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"


@patch('app.account.routes.conn')
def test_get_account_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.get('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"


################################
# update_account endpoint tests#
################################

# Test 1: Update account success
@patch('app.account.routes.conn')
def test_update_account_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.rowcount = 1  # Simulate successful update

    data = {
        "username": "new_username",
        "phone": "1234567890"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account updated successfully"

# Test 2: Invalid UUID format
def test_update_account_invalid_uuid(client):
    data = {
        "username": "new_username"
    }
    response = client.patch(f'/account/{INVALID_UUID}', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format"

# Test 3: No valid fields to update
def test_update_account_no_fields(client):
    data = {}  # Empty body, no fields to update
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "No valid fields to update"

# Test 4: Account not found
@patch('app.account.routes.conn')
def test_update_account_not_found(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.rowcount = 0  # Simulate account not found

    data = {
        "username": "new_username"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"

# Test 5: Unique violation on username
@patch('app.account.routes.conn')
def test_update_account_username_exists(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation("duplicate key value violates unique constraint \"account_username_key\"")

    data = {
        "username": "existing_username"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Username already exists."

# Test 6: Unique violation on phone number
@patch('app.account.routes.conn')
def test_update_account_phone_exists(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation("duplicate key value violates unique constraint \"account_phone_key\"")

    data = {
        "phone": "1234567890"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Phone number already exists."

# Test 7: Unexpected error during update
@patch('app.account.routes.conn')
def test_update_account_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    data = {
        "username": "new_username"
    }
    response = client.patch(f'/account/{VALID_UUID}', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"


##################################
# update_status endpoint Testing #
##################################
# update_status endpoint Testing'
# Test 1: Successful status update to 'active'
@patch('app.account.routes.conn')
def test_update_account_status_active_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (VALID_UUID,)  # Simulate account found

    data = {
        "status": "active"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account status updated to active successfully"

# Test 2: Successful status update to 'disabled'
@patch('app.account.routes.conn')
def test_update_account_status_disabled_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (VALID_UUID,)  # Simulate account found

    data = {
        "status": "disabled"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account status updated to disabled successfully"

# Test 3: Invalid status provided
def test_update_account_status_invalid_status(client):
    data = {
        "status": "unknown_status"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid status. Allowed values are 'active' or 'disabled'."

# Test 4: Account not found
@patch('app.account.routes.conn')
def test_update_account_status_account_not_found(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Simulate account not found

    data = {
        "status": "active"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"

# Test 5: Unexpected error during status update
@patch('app.account.routes.conn')
def test_update_account_status_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    data = {
        "status": "active"
    }
    response = client.put(f'/account/{VALID_UUID}/status', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"


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
@patch('app.account.routes.conn')
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
@patch('app.account.routes.conn')
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
@patch('app.account.routes.conn')
def test_get_accounts_by_status_no_accounts_found(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []  # Simulate no accounts found

    response = client.get('/account/accounts?status=active')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "No accounts found."

# Test 5: Unexpected error during fetching
@patch('app.account.routes.conn')
def test_get_accounts_by_status_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.get('/account/accounts?status=active')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"


###################################
# delete_account endpoint Testing #
###################################

# Test for successful deletion of an account
@patch('app.account.routes.conn')
def test_delete_account_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'account_id': '123e4567-e89b-12d3-a456-426614174000'}

    response = client.delete('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Account and associated records deleted successfully"
    mock_cursor.execute.assert_called()


# Test for invalid account ID format
def test_delete_account_invalid_id_format(client):
    response = client.delete('/account/invalid-id')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format"


# Test for account not found
@patch('app.account.routes.conn')
def test_delete_account_not_found(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Simulate no account found

    response = client.delete('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"


# Test for unexpected error during deletion
@patch('app.account.routes.conn')
def test_delete_account_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.delete('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"



################################
# search_accounts endpoint tests#
################################

# Test for empty search term
def test_search_accounts_empty_term(client):
    response = client.get('/account/accounts/search?q=')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Search term cannot be empty."

# Test for no accounts found
@patch('app.account.routes.conn')
def test_search_accounts_not_found(mock_conn, client):
    search_term = "nonexistent"
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []  # Simulate no accounts found

    response = client.get(f'/account/accounts/search?q={search_term}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "No accounts found."

# Test for successful search
@patch('app.account.routes.conn')
def test_search_accounts_success(mock_conn, client):
    search_term = "john"
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            'account_id': '123e4567-e89b-12d3-a456-426614174000',
            'account_username': 'john_doe',
            'account_fullname': 'John Doe',
            'account_phone': '123-456-7890',
        },
        {
            'account_id': '123e4567-e89b-12d3-a456-426614174001',
            'account_username': 'john_smith',
            'account_fullname': 'John Smith',
            'account_phone': '098-765-4321',
        },
    ]  # Simulate found accounts

    response = client.get(f'/account/accounts/search?q={search_term}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert len(result) == 2  # Ensure two accounts were found
    assert result[0]['account_username'] == 'john_doe'  # Check first account details
    assert result[1]['account_username'] == 'john_smith'  # Check second account details

# Test for unexpected error during search
@patch('app.account.routes.conn')
def test_search_accounts_unexpected_error(mock_conn, client):
    search_term = "john"
    mock_cursor = MagicMock()

    # Set up the mock connection to return the mock cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Set the side effect of the execute method to raise an Exception
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    # Call the endpoint
    response = client.get(f'/account/accounts/search?q={search_term}')

    # Assert the expected response
    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"



################################
# create_email endpoint tests ##
################################

 #Assuming you have a function named validate_email_address in your codebase
# def mock_validate_email_address(email):
#     return '@' in email  # Simple mock for email validation
#
# # Test cases
# @patch('app.email.routes.conn')
# @patch('app.email.routes.validate_email_address', side_effect=mock_validate_email_address)
# def test_create_email_missing_fields(mock_validate, mock_conn, client):
#     response = client.post('/email', json={})
#     assert response.status_code == 400
#     assert response.json['message'] == "Missing required fields: account_id or email."
#
# @patch('app.email.routes.conn')
# @patch('app.email.routes.validate_email_address', side_effect=mock_validate_email_address)
# def test_create_email_invalid_account_id(mock_validate, mock_conn, client):
#     response = client.post('/email', json={"account_id": "invalid-uuid", "email": "test@example.com"})
#     assert response.status_code == 400
#     assert response.json['message'] == "Invalid account ID format"
#
# @patch('app.email.routes.conn')
# @patch('app.email.routes.validate_email_address', side_effect=mock_validate_email_address)
# def test_create_email_invalid_email_format(mock_validate, mock_conn, client):
#     response = client.post('/email', json={"account_id": str(UUID(int=1)), "email": "invalid-email"})
#     assert response.status_code == 400
#     assert response.json['message'] == "Invalid email format."
#
# @patch('app.email.routes.conn')
# @patch('app.email.routes.validate_email_address', side_effect=mock_validate_email_address)
# def test_create_email_success(mock_validate, mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_cursor.fetchone.return_value = {'email_id': 1}  # Mock returning email_id
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#
#     response = client.post('/email', json={"account_id": str(UUID(int=1)), "email": "test@example.com"})
#     assert response.status_code == 201
#     assert response.json['message'] == "Email created successfully"
#     assert response.json['email_id'] == 1
#
# @patch('app.email.routes.conn')
# @patch('app.email.routes.validate_email_address', side_effect=mock_validate_email_address)
# def test_create_email_already_exists(mock_validate, mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#     mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation("Unique violation")
#
#     response = client.post('/email', json={"account_id": str(UUID(int=1)), "email": "test@example.com"})
#     assert response.status_code == 409
#     assert response.json['message'] == "Email already exists."
#
# @patch('app.email.routes.conn')
# @patch('app.email.routes.validate_email_address', side_effect=mock_validate_email_address)
# def test_create_email_account_not_found(mock_validate, mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#     mock_cursor.execute.side_effect = psycopg2.errors.ForeignKeyViolation("Foreign key violation")
#
#     response = client.post('/email', json={"account_id": str(UUID(int=1)), "email": "test@example.com"})
#     assert response.status_code == 404
#     assert response.json['message'] == "Account not found."
#
# @patch('app.email.routes.conn')
# @patch('app.email.routes.validate_email_address', side_effect=mock_validate_email_address)
# def test_create_email_unexpected_error(mock_validate, mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#     mock_cursor.execute.side_effect = Exception("Unexpected error")
#
#     response = client.post('/email', json={"account_id": str(UUID(int=1)), "email": "test@example.com"})
#     assert response.status_code == 500
#     assert "error" in response.json  # Check that there's an error message



# @patch('app.account.routes.conn')
# def test_get_account_non_existent(mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#
#     # Mock the cursor to return None, simulating a non-existent account
#     mock_cursor.fetchone.return_value = None
#
#     # Use a valid UUID format, but for a non-existent account
#     response = client.get('/account/123e4567-e89b-12d3-a456-426614174000')
#     assert response.status_code == 404
#     data = json.loads(response.data)
#     assert data['message'] == "Account not found"
#
#     # Verify that the correct SQL query was executed
#     mock_cursor.execute.assert_called_once()
#     sql_query = mock_cursor.execute.call_args[0][0]
#     assert "SELECT * FROM account WHERE account_id = %s" in sql_query


# @patch('app.account.routes.conn')
# def test_get_account(mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#
#     # Mock UUID for the test
#     test_uuid = UUID('12345678-1234-5678-1234-567812345678')
#
#     # Mock the return values for each cursor call (fetchone for account, fetchall for emails, fetchone for telegram)
#     mock_cursor.fetchone.side_effect = [
#         {'account_id': test_uuid, 'username': 'testuser'},  # Account fetch
#         {'telegram_user_id': '987654321', 'telegram_username': 'test_telegram'}  # Telegram fetch
#     ]
#     mock_cursor.fetchall.return_value = [{'email_id': 1, 'email': 'test@example.com'}]  # Emails fetch
#
#     # Perform GET request to the route
#     response = client.get(f'/account/{test_uuid}')
#
#     # Assertions
#     assert response.status_code == 200
#     data = json.loads(response.data)
#     assert data['account_id'] == str(test_uuid)
#     assert data['username'] == 'testuser'
#
#     # Check emails
#     assert len(data['emails']) == 1
#     assert data['emails'][0]['email'] == 'test@example.com'
#
#     # Check telegram information
#     assert data['telegram']['telegram_user_id'] == '987654321'
#     assert data['telegram']['telegram_username'] == 'test_telegram'



# @patch('app.account.routes.conn')
# def test_get_all_accounts(mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#
#     # Mock data including all fields from account, email, and telegram tables
#     mock_cursor.fetchall.return_value = [
#         {
#             'account_id': '550e8400-e29b-41d4-a716-446655440000',
#             'account_username': 'user1',
#             'account_fullname': 'User One',
#             'account_is_admin': True,
#             'email_id': '550e8400-e29b-41d4-a716-446655440001',
#             'email_address': 'user1@example.com',
#             'email_account_id': '550e8400-e29b-41d4-a716-446655440000',
#             'telegram_id': '550e8400-e29b-41d4-a716-446655440002',
#             'telegram_user_id': '12345',
#             'telegram_username': 'user1_telegram',
#             'telegram_account_id': '550e8400-e29b-41d4-a716-446655440000'
#         },
#         {
#             'account_id': '550e8400-e29b-41d4-a716-446655440000',
#             'account_username': 'user1',
#             'account_fullname': 'User One',
#             'account_is_admin': True,
#             'email_id': '550e8400-e29b-41d4-a716-446655440003',
#             'email_address': 'user1_alt@example.com',
#             'email_account_id': '550e8400-e29b-41d4-a716-446655440000',
#             'telegram_id': '550e8400-e29b-41d4-a716-446655440002',
#             'telegram_user_id': '12345',
#             'telegram_username': 'user1_telegram',
#             'telegram_account_id': '550e8400-e29b-41d4-a716-446655440000'
#         },
#         {
#             'account_id': '660e8400-e29b-41d4-a716-446655440000',
#             'account_username': 'user2',
#             'account_fullname': 'User Two',
#             'account_is_admin': False,
#             'email_id': '660e8400-e29b-41d4-a716-446655440001',
#             'email_address': 'user2@example.com',
#             'email_account_id': '660e8400-e29b-41d4-a716-446655440000',
#             'telegram_id': None,
#             'telegram_user_id': None,
#             'telegram_username': None,
#             'telegram_account_id': None
#         }
#     ]
#
#     response = client.get('/account/all')
#     assert response.status_code == 200
#     data = json.loads(response.data)
#
#     assert len(data) == 2  # Two unique accounts
#
#     # Check first account (user1)
#     assert data[0]['account']['account_id'] == '550e8400-e29b-41d4-a716-446655440000'
#     assert data[0]['account']['account_username'] == 'user1'
#     assert data[0]['account']['account_fullname'] == 'User One'
#     assert data[0]['account']['account_is_admin'] is True
#     assert len(data[0]['emails']) == 2
#     assert data[0]['emails'][0]['email_id'] == '550e8400-e29b-41d4-a716-446655440001'
#     assert data[0]['emails'][0]['email_address'] == 'user1@example.com'
#     assert data[0]['emails'][1]['email_id'] == '550e8400-e29b-41d4-a716-446655440003'
#     assert data[0]['emails'][1]['email_address'] == 'user1_alt@example.com'
#     assert data[0]['telegram'] is not None
#     assert data[0]['telegram']['telegram_id'] == '550e8400-e29b-41d4-a716-446655440002'
#     assert data[0]['telegram']['telegram_user_id'] == '12345'
#     assert data[0]['telegram']['telegram_username'] == 'user1_telegram'
#
#     # Check second account (user2)
#     assert data[1]['account']['account_id'] == '660e8400-e29b-41d4-a716-446655440000'
#     assert data[1]['account']['account_username'] == 'user2'
#     assert data[1]['account']['account_fullname'] == 'User Two'
#     assert data[1]['account']['account_is_admin'] is False
#     assert len(data[1]['emails']) == 1
#     assert data[1]['emails'][0]['email_id'] == '660e8400-e29b-41d4-a716-446655440001'
#     assert data[1]['emails'][0]['email_address'] == 'user2@example.com'
#     assert data[1]['telegram'] is None
#
#     # Verify that the SQL query includes the telegram table and correct ordering
#     mock_cursor.execute.assert_called_once()
#     sql_query = mock_cursor.execute.call_args[0][0]
#     assert 'LEFT JOIN telegram t ON t.telegram_account_id = a.account_id' in sql_query
#     assert 'ORDER BY a.account_is_admin DESC, a.account_fullname ASC' in sql_query
#
#
#
# @patch('app.account.routes.conn')
# def test_update_account(mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#
#     data = {
#         'username': 'updateduser',
#         'fullname': 'Updated User',
#         'phone': '0987654321',
#         'password_hash': 'new_hashed_password'
#     }
#     response = client.put('/account/1', json=data)
#     assert response.status_code == 200
#     result = json.loads(response.data)
#     assert result['message'] == "Account updated successfully"
#
#
# @patch('app.account.routes.conn')
# def test_delete_account(mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#
#     response = client.delete('/account/1')
#     assert response.status_code == 200
#     result = json.loads(response.data)
#     assert result['message'] == "Account and associated emails deleted successfully"


# @patch('app.account.routes.conn')
# def test_create_email(mock_conn, client):
#     mock_cursor = MagicMock()
#     mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
#     mock_cursor.fetchone.return_value = {'email_id': 1}
#
#     data = {
#         'account_id': 1,
#         'email': 'test@example.com'
#     }
#     response = client.post('/account/email', json=data)
#     assert response.status_code == 201
#     result = json.loads(response.data)
#     assert result['message'] == "Email created successfully"
#     assert result['email_id'] == 1
#
#
# @patch('app.account.routes.conn')
# def test_get_account_invalid_uuid(mock_conn, client):
#     # Test with an invalid UUID
#     response = client.get('/account/not-a-valid-uuid')
#     assert response.status_code == 400
#     data = json.loads(response.data)
#     assert data['message'] == "Invalid account ID format"
#


