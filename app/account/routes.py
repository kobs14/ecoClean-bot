import logging
from uuid import UUID

import bcrypt
import psycopg2
from flask import Blueprint, jsonify, request, current_app
from psycopg2.extras import RealDictCursor

from app.account.validators import validate_email_address, validate_field
from app.main import global_conn as conn
from app.config import logger

bp = Blueprint('account', __name__)


@bp.route('/test')
def test():
    """
    Test route to verify that the server is running.

    Returns:
        str: A message confirming the test route is working.
    """
    logger.info("Test route accessed")
    return "Test route is working"


@bp.route('/routes')
def list_routes():
    """
    Lists all routes registered with this blueprint.

    Returns:
        flask.Response: A JSON object containing the list of routes.
    """
    logger.info("Listing available routes")

    routes = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint.startswith(bp.name):
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "route": str(rule)
            })

    logger.info(f"Found {len(routes)} routes")
    return jsonify(routes)


@bp.route('/db-test')
def db_test():
    """
    Tests the database connection.

    This function attempts to execute a simple SQL query to verify if the database
    connection is working. If successful, it returns a confirmation message along with the query result.
    If the connection fails, an error message is returned.

    Returns:
        flask.Response: A JSON object containing the success or failure message.
        On success: {"message": "Database connection successful", "result": result}
        On failure: {"message": "Database connection failed", "error": str(e)}
    """

    logger.info("Testing database connection")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        logger.info("Database connection successful")
        return jsonify({"message": "Database connection successful", "result": result})

    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return jsonify({"message": "Database connection failed", "error": str(e)}), 500



@bp.route('/register', methods=['POST'])
def create_account():
    """
    Create a new account.

    This endpoint receives account information, validates the input,
    and creates a new account in the database.

    Request JSON format:
    {
        "username": "string",
        "fullname": "string",
        "phone": "string",
        "password": "string",
        "is_admin": "boolean", (optional)
        "commission_rate": "decimal", (optional)
        "status": "string" (optional, defaults to "active")
    }

    Returns:
        - 201: Account created successfully with account ID.
        - 400: Missing required field or invalid phone format.
        - 409: Username or phone number already exists.
        - 500: Unexpected error occurred.
    """

    data = request.json
    logger.info(f"Received request to create account with username: {data.get('username')}")

    required_fields = {
        'account_username': 'username',
        'account_fullname': 'fullname',
        'account_phone': 'phone',
        'account_password_hash': 'password'
    }

    account_data = {}

    # Validate required fields
    for field, json_key in required_fields.items():
        if json_key not in data:
            return jsonify({"message": f"Missing required field: {json_key}"}), 400
        try:
            account_data[field] = validate_field(field, data[json_key])
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    # Validate optional fields
    optional_fields = {
        'account_is_admin': 'is_admin',
        'account_commission_rate': 'commission_rate',
        'account_status': 'status'
    }

    for field, json_key in optional_fields.items():
        if json_key in data:
            try:
                account_data[field] = validate_field(field, data[json_key])
            except ValueError as e:
                return jsonify({"message": str(e)}), 400

    try:
        # Hash the password
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO account (account_username, account_fullname, account_phone, 
                   account_password_hash, account_is_admin, account_commission_rate, account_status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (account_data['account_username'], account_data['account_fullname'],
                 account_data['account_phone'], account_data['account_password_hash'],
                 account_data.get('account_is_admin', False),
                 account_data.get('account_commission_rate', 0.00),
                 account_data.get('account_status', 'active'))
            )
        conn.commit()
        logger.info(f"Account created successfully: {account_data['account_username']}")
        return jsonify({"message": "Account created successfully"}), 201

    except psycopg2.errors.UniqueViolation as e:
        # Check if the error is related to username or phone
        if 'account_username' in str(e):
            logger.error(f"Username already exists: {data['username']}.")
            conn.rollback()
            return jsonify({"message": "Username already exists."}), 409
        elif 'account_phone' in str(e):
            logger.error(f"Phone number already exists: {data['phone']}.")
            conn.rollback()
            return jsonify({"message": "Phone number already exists."}), 409
        else:
            logger.error(f"Error creating account: {str(e)}")
            conn.rollback()
            return jsonify({"error": "An unexpected error occurred."}), 50

    except Exception as e:
        conn.rollback()  # Rollback the transaction on error
        logger.error(f"Error creating account: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/all', methods=['GET'])
def get_all_accounts():
    """
    Fetches all accounts from the database, including related email and Telegram details.

    This function performs a LEFT JOIN between the account, email, and telegram tables to retrieve
    all account details, along with any associated email addresses and Telegram information.
    Accounts are ordered by admin status and full name.

    Returns:
        flask.Response: A JSON object containing the account details, emails, and Telegram information.
        On error: A JSON object with an error message and HTTP status code 500.
    """

    logger.info("Fetching all accounts")

    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT a.*, e.*, t.*
                FROM account a
                LEFT JOIN email e ON e.email_account_id = a.account_id
                LEFT JOIN telegram t ON t.telegram_account_id = a.account_id
                ORDER BY a.account_is_admin DESC, a.account_fullname ASC;
            ''')
            rows = cur.fetchall()

        accounts = {}
        for row in rows:
            account_id = row['account_id']
            if account_id not in accounts:
                accounts[account_id] = {
                    'account': {k: v for k, v in row.items() if k.startswith('account_')},
                    'emails': [],
                    'telegram': None
                }

            if row['email_id']:
                accounts[account_id]['emails'].append({k: v for k, v in row.items() if k.startswith('email_')})

            if row['telegram_id']:
                accounts[account_id]['telegram'] = {k: v for k, v in row.items() if k.startswith('telegram_')}

        logger.info(f"Successfully fetched {len(accounts)} accounts")
        return jsonify(list(accounts.values()))

    except Exception as e:
        logger.error(f"Error fetching accounts: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/<id>', methods=['GET'])
def get_account(id):
    """
    Fetches an account and its associated emails and Telegram info by account ID.

    Args:
        id (str): The unique identifier of the account (UUID format).

    Returns:
        jsonify: A JSON response containing the account details, including associated emails
                  and Telegram info, or an error message if the account is not found or
                  if the ID format is invalid.
    """
    logger.debug(f"Attempting to fetch account with ID: {id}")

    # Validate the account ID format
    try:
        account_id = str(UUID(id))  # Convert UUID to string for psycopg2
    except ValueError:
        logger.error("Invalid account ID format received.")
        return jsonify({"message": "Invalid account ID format"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Fetch account details
            cursor.execute("SELECT * FROM account WHERE account_id = %s", (account_id,))
            account = cursor.fetchone()

            if account is None:
                logger.warning(f"Account with ID: {id} not found.")
                return jsonify({"message": "Account not found"}), 404

            # Fetch associated emails
            cursor.execute("SELECT * FROM email WHERE email_account_id = %s", (account_id,))
            emails = cursor.fetchall()

            # Fetch associated Telegram info
            cursor.execute("SELECT * FROM telegram WHERE telegram_account_id = %s", (account_id,))
            telegram = cursor.fetchone()

            # Add emails and telegram info to the account details
            account['emails'] = emails
            account['telegram'] = telegram


        logger.info(f"Successfully fetched account with ID: {id}.")
        return jsonify(account)

    except Exception as e:
        logger.error(f"Error fetching account with ID: {id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/<id>', methods=['PATCH'])
def update_account(id):
    """
    Update specific fields of an account identified by its UUID.

    This endpoint allows clients to update one or more fields of an account.
    Only the fields provided in the request body will be updated.
    If a field is not included in the request, it will remain unchanged.

    Args:
        id (str): The UUID of the account to be updated. This is extracted from the URL.

    Returns:
        Response: A JSON response indicating the result of the operation. Possible responses include:
            - 200: Successfully updated the account.
            - 400: Invalid account ID format or no valid fields to update.
            - 404: Account not found for the provided ID.
            - 500: An error occurred while attempting to update the account.

    Example:
        PATCH /account/123e4567-e89b-12d3-a456-426614174000
        {
            "username": "new_username",
            "phone": "+1234567890"
        }

    Notes:
        The following fields are valid for updating:
        -username
        -fullname
        -phone
        -password
        -is_admin
        -commission_rate
        -status

        If an invalid account ID is provided, the function returns a 400 response.
        If no valid fields are provided for the update, a 400 response is also returned.
        The last update timestamp is automatically recorded during the update.
    """
    logger.info(f"Received request to update account with ID: {id}")

    # Validate the account ID format
    try:
        account_id = str(UUID(id))
    except ValueError:
        logger.error("Invalid account ID format received.")
        return jsonify({"message": "Invalid account ID format"}), 400

    data = request.json

    # Updated valid_fields dictionary
    valid_fields = {
        'username': 'account_username',
        'fullname': 'account_fullname',
        'phone': 'account_phone',
        'password': 'account_password_hash',
        'is_admin': 'account_is_admin',
        'commission_rate': 'account_commission_rate',
        'status': 'account_status'
    }

    # Construct update_fields with correct database field names
    update_fields = {}
    for input_field, db_field in valid_fields.items():
        if input_field in data:
            try:
                update_fields[db_field] = validate_field(db_field, data[input_field])
            except ValueError as e:
                return jsonify({"message": f"Invalid value for {input_field}: {str(e)}"}), 400

    # Check if there are valid fields to update
    if not update_fields:
        return jsonify({"message": "No valid fields to update"}), 400

    logger.info(f"Updating fields for account ID: {id}: {update_fields}")

    # Hash the password if it's being updated
    if 'account_password_hash' in update_fields:
        update_fields['account_password_hash'] = bcrypt.hashpw(update_fields['account_password_hash'].encode('utf-8'),
                                                               bcrypt.gensalt())

    # Construct the SQL query dynamically
    set_clause = ", ".join([f"{k} = %s" for k in update_fields.keys()])
    query = f"UPDATE account SET {set_clause}, account_updated_at = CURRENT_TIMESTAMP WHERE account_id = %s"
    params = list(update_fields.values()) + [account_id]

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if cursor.rowcount == 0:
                logger.warning(f"Account with ID: {id} not found.")
                return jsonify({"message": "Account not found"}), 404
            conn.commit()  # Commit the transaction if the update is successful
        logger.info(f"Account with ID: {id} updated successfully. Updated fields: {update_fields}")
        return jsonify({"message": "Account updated successfully"}), 200

    except psycopg2.errors.UniqueViolation as e:
        # Check if the error is related to username or phone
        if 'account_username' in str(e):
            logger.error(f"Username already exists: {data['username']}.")
            conn.rollback()
            return jsonify({"message": "Username already exists."}), 409
        elif 'account_phone' in str(e):
            logger.error(f"Phone number already exists: {data['phone']}.")
            conn.rollback()
            return jsonify({"message": "Phone number already exists."}), 409
        else:
            logger.error(f"Error creating account: {str(e)}")
            conn.rollback()
            return jsonify({"error": "An unexpected error occurred."}), 50

    except Exception as e:
        conn.rollback()  # Rollback the transaction on error
        logger.error(f"Error updating account with ID: {id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


# TODO: Implement authorization
@bp.route('/<id>', methods=['DELETE'])
def delete_account(id):
    """
    Delete an account and all associated records.

    This endpoint removes the specified account from the system along with any
    associated records in the Telegram and email tables. The deletion of
    associated Telegram records is handled automatically due to the
    ON DELETE CASCADE constraint.

    Args:
        id (str): The UUID of the account to be deleted. This is extracted from the URL.

    Returns:
        Response: A JSON response indicating the result of the operation. Possible responses include:
            - 200: Successfully deleted the account and associated records.
            - 400: Invalid account ID format.
            - 404: Account not found for the provided ID.
            - 500: An error occurred while attempting to delete the account.

    Example:
        DELETE /account/123e4567-e89b-12d3-a456-426614174000
    """
    logger.info(f"Received request to delete account with ID: {id}")
    # Validate the account ID format
    try:
        account_id = str(UUID(id))
    except ValueError:
        logger.error("Invalid account ID format received.")
        return jsonify({"message": "Invalid account ID format"}), 400

    try:
        # Ensure the account exists before attempting to delete
        with conn.cursor() as cursor:
            cursor.execute("SELECT account_id FROM account WHERE account_id = %s", (id,))
            account = cursor.fetchone()

            if not account:
                logger.warning(f"Account with ID: {id} not found.")
                return jsonify({"message": "Account not found"}), 404

            # Delete associated Telegram records
            logger.info(f"Deleting associated Telegram records for account ID: {id}")
            cursor.execute("DELETE FROM telegram WHERE telegram_account_id = %s", (id,))

            # Delete associated email records
            logger.info(f"Deleting associated email records for account ID: {id}")
            cursor.execute("DELETE FROM email WHERE email_account_id = %s", (id,))

            # Delete the account
            logger.info(f"Deleting account with ID: {id}")
            cursor.execute("DELETE FROM account WHERE account_id = %s", (id,))
            conn.commit()

        logger.info(f"Account and associated records deleted successfully for account ID: {id}")
        return jsonify({"message": "Account and associated records deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting account with ID: {id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


# TODO: Implement authorization
@bp.route('/<id>/status', methods=['PUT'])
def update_account_status(id):
    """
    Update the status of an account.
    The status can only be updated to 'active' or 'disabled'.

    Args:
        id (str): The UUID of the account to update.

    Returns:
        Response:
            - 200 if the account status was successfully updated.
            - 400 if an invalid status is provided.
            - 404 if the account is not found.
            - 500 in case of a server error.

    Example:
        PUT /account/69b107b2-3ec2-4b21-be4e-4e4e85b28421/status
        Payload: {"status": "active"}

    """
    logger.info(f"Received request to update account status for account ID: {id}")

    # Parse JSON data
    data = request.json
    new_status = data.get('status')
    logger.debug(f"Requested new status: {new_status}")

    # Validate the status
    if new_status not in ['active', 'disabled']:
        logger.warning(f"Invalid status '{new_status}' provided for account ID: {id}")
        return jsonify({"message": "Invalid status. Allowed values are 'active' or 'disabled'."}), 400

    try:
        # Update the account status in the database
        with conn.cursor() as cursor:
            logger.info(f"Updating account status to '{new_status}' for account ID: {id}")
            cursor.execute(
                "UPDATE account SET account_status = %s WHERE account_id = %s RETURNING account_id",
                (new_status, str(id))
            )
            updated_account_id = cursor.fetchone()

        # Check if the account exists and was updated
        if updated_account_id:
            conn.commit()
            logger.info(f"Account status successfully updated to '{new_status}' for account ID: {id}")
            return jsonify({"message": f"Account status updated to {new_status} successfully"}), 200
        else:
            logger.warning(f"Account with ID: {id} not found for status update")
            return jsonify({"message": "Account not found"}), 404

    except Exception as e:
        # Log and return the error
        logger.error(f"Error updating account status for account ID: {id}: {str(e)}")
        return jsonify({"error": str(e)}), 500



@bp.route('/accounts', methods=['GET'])
def get_accounts_by_status():
    """
    Fetches accounts from the database based on their status.

    Expects a query parameter:
        status: The status of the accounts to fetch. Allowed values are 'active' or 'disabled'.

    Returns:
        jsonify: A JSON response containing the list of accounts with the specified status
                 or an error message if the status is invalid or no accounts are found.
    """
    status = request.args.get('status')  # Get status from the query parameter
    logger.info(f"Fetching accounts with status: {status}")

    if status not in ['active', 'disabled']:
        logger.warning(f"Invalid status provided: {status}. Allowed values are 'active' or 'disabled'.")
        return jsonify({"message": "Invalid status. Allowed values are 'active' or 'disabled'."}), 400

    try:
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT * FROM account
                    WHERE account_status = %s
                    ORDER BY account_fullname ASC;
                """, (status,))
            accounts = cur.fetchall()

        if not accounts:
            logger.info(f"No accounts found with status: {status}.")
            return jsonify({"message": "No accounts found."}), 404

        logger.info(f"Found {len(accounts)} accounts with status: {status}.")
        return jsonify(accounts)  # Consider formatting this response

    except Exception as e:
        logger.error(f"Unexpected error while fetching accounts: {str(e)}")
        return jsonify({"error": "Unexpected error"}), 500


@bp.route('/accounts/search', methods=['GET'])
def search_accounts():
    search_term = request.args.get('q', '')
    logger.info(f"Searching accounts with term: {search_term}")

    # Check if the search term is empty
    if not search_term:
        logger.warning("Search term is empty.")
        return jsonify({"message": "Search term cannot be empty."}), 400

    try:
        # Perform the search in the database
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM account
                WHERE account_username ILIKE %s
                OR account_fullname ILIKE %s
                OR account_phone ILIKE %s
                ORDER BY account_fullname ASC;
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            accounts = cur.fetchall()

        # Check if any accounts were found
        if not accounts:
            logger.info("No accounts found matching the search term.")
            return jsonify({"message": "No accounts found."}), 404

        logger.info(f"Found {len(accounts)} accounts matching the search term.")
        return jsonify(accounts)

    except Exception as e:
        logger.error(f"Error occurred while searching for accounts: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/email', methods=['POST'])
def create_email():
    """
    Create a new email associated with an account.

    This endpoint receives an account ID and an email address, validates
    the input, and creates a new email entry in the database.

    Request JSON format:
    {
        "account_id": "UUID",
        "email": "string"
    }

    Returns:
        - 201: Email created successfully with email ID.
        - 400: Missing required fields or invalid email format.
        - 409: Email already exists.
        - 500: Unexpected error occurred.
    """

    data = request.json
    logger.info(f"Creating email for account ID: {data.get('account_id')} with email: {data.get('email')}")

    # Check for missing required fields
    if not data.get('account_id') or not data.get('email'):
        logger.warning("Missing required fields: account_id or email.")
        return jsonify({"message": "Missing required fields: account_id or email."}), 400
    # Validate account_id format
    try:
        account_id = str(UUID(data.get('account_id')))  # Convert UUID to string for psycopg2
    except ValueError:
        logger.error("Invalid account ID format received.")
        return jsonify({"message": "Invalid account ID format"}), 400

    # Validate email format
    if not validate_email_address(data['email']):
        return jsonify({"message": "Invalid email format."}), 400

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO email (email_account_id, email_address) "
                "VALUES (%s, %s) RETURNING email_id",
                (account_id, data['email'])
            )
            email_id = cursor.fetchone()['email_id']  # Get the newly created email ID
            conn.commit()  # Commit the transaction

        logger.info(f"Email created successfully with ID: {email_id} for account ID: {data['account_id']}.")
        return jsonify({"message": "Email created successfully", "email_id": email_id}), 201

    except psycopg2.errors.UniqueViolation:
        logger.error(f"Email {data['email']} already exists.")
        conn.rollback()  # Rollback the transaction
        return jsonify({"message": "Email already exists."}), 409

    except psycopg2.errors.ForeignKeyViolation:
        logger.error(f"Account with ID: {data['account_id']} does not exist.")
        conn.rollback()  # Rollback the transaction
        return jsonify({"message": "Account not found."}), 404

    except Exception as e:
        logger.error(f"Error creating email for account ID: {data['account_id']}: {str(e)}")
        conn.rollback()  # Rollback the transaction on general error
        return jsonify({"error": str(e)}), 500



#################################################################################
# ALL ABOVE TESTED AND VERIFIED
#################################################################################

