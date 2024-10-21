
# app/telegram/routes.py


from uuid import UUID

from flask import Blueprint, jsonify, request
import traceback
from psycopg2 import sql
from psycopg2 import errors as psycopg2_errors
from psycopg2.extras import RealDictCursor

from app.main import global_conn as conn
from app.config import logger

telegram_bp = Blueprint('telegram', __name__)

@telegram_bp.route('/link', methods=['POST'])
def link_telegram_account():
    """
    Create a new Telegram entry associated with an account.

    Request JSON format:
    {
        "telegram_account_id": "UUID",       # The ID of the user account from the 'account' table (must be a valid UUID).
        "telegram_user_id": "string",        # Unique identifier for the Telegram user (required).
        "telegram_username": "string",       # Unique Telegram username (optional).
        "telegram_verified": "boolean"       # Whether the Telegram account is verified (default is False if not provided).
        "telegram_is_admin": "boolean"
    }

    Responses:
        - 201: Telegram entry created successfully.
          Example:
          {
            "message": "Telegram entry created successfully",
            "telegram_id": "UUID"            # The ID of the newly created Telegram entry.
          }
        - 400: Bad request due to missing required fields or invalid data format.
          Example:
          {
            "message": "Missing required fields: telegram_account_id or telegram_user_id."
          }
          or
          {
            "message": "Invalid telegram_account_id format."
          }
        - 404: The account with the provided 'telegram_account_id' was not found.
          Example:
          {
            "message": "Account not found."
          }
        - 500: Internal server error, such as a database issue or unexpected exception.
          Example:
          {
            "error": "Detailed error message describing the problem."
          }
    """
    data = request.json
    logger.info(f"Attempting to create Telegram entry with data: {data}")

    required_fields = ['telegram_account_id', 'telegram_user_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
        return jsonify({"message": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        telegram_account_id = str(UUID(data['telegram_account_id']))
    except ValueError:
        logger.error(f"Invalid telegram account ID format received: {data['telegram_account_id']}")
        return jsonify({"message": "Invalid telegram account ID format."}), 400

    telegram_user_id = data['telegram_user_id']
    telegram_username = data.get('telegram_username')
    telegram_verified = data.get('telegram_verified', False)
    telegram_is_admin = data.get('telegram_is_admin', False)

    query = sql.SQL(
        "INSERT INTO telegram (telegram_account_id, telegram_user_id, telegram_username, telegram_verified, telegram_is_admin) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING telegram_id"
    )
    params = (telegram_account_id, telegram_user_id, telegram_username, telegram_verified, telegram_is_admin)

    try:
        logger.info(f"Executing SQL query: {query.as_string(conn)} with params: {params}")
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            if result is None:
                logger.error("INSERT operation did not return a result. This might indicate a constraint violation.")
                conn.rollback()
                return jsonify({"message": "Failed to create Telegram entry. Possible constraint violation."}), 400

            # telegram_id = result[0]
            conn.commit()

        logger.info(
            # f"Telegram entry created successfully with ID: {telegram_id} for telegram account ID: {telegram_account_id}")
            f"Telegram entry created successfully with Username: {telegram_username} for telegram account ID: {telegram_account_id}")
        return jsonify({"message": "Telegram entry created successfully", "telegram_username": telegram_username}), 201

    except psycopg2_errors.ForeignKeyViolation as e:
        logger.error(f"Foreign key violation. Account with ID: {telegram_account_id} does not exist. Error: {str(e)}")
        conn.rollback()
        return jsonify(
            {"message": "Account not found. Please ensure the account exists before linking a Telegram."}), 404
    except psycopg2_errors.UniqueViolation as e:
        conn.rollback()
        if 'telegram_user_id' in str(e):
            logger.error(f"Unique constraint violation on telegram_user_id. Error: {str(e)}")
            return jsonify({"message": "A Telegram entry with this user ID already exists."}), 409
        elif 'telegram_username' in str(e):
            logger.error(f"Unique constraint violation on telegram_username. Error: {str(e)}")
            return jsonify({"message": "A Telegram entry with this username already exists."}), 409
        else:
            logger.error(f"Unique constraint violation. Error: {str(e)}")
            return jsonify({"message": "A Telegram entry with these details already exists."}), 409
    except psycopg2_errors.CheckViolation as e:
        logger.error(f"Check constraint violation. Error: {str(e)}")
        conn.rollback()
        return jsonify({"message": "The provided data violates a check constraint."}), 400
    except psycopg2_errors.Error as e:
        logger.error(f"Database error occurred: {e.pgerror}. SQL State: {e.pgcode}")
        conn.rollback()
        return jsonify({"message": "A database error occurred.", "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error creating Telegram entry for telegram account ID: {telegram_account_id}.")
        logger.error(f"Error details: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        conn.rollback()
        return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500



@telegram_bp.route('/<telegram_id>', methods=['GET'])
def get_telegram(telegram_id):
    """
    Retrieve a Telegram entry by its telegram_id.

    Args:
        telegram_id (UUID): The unique ID of the Telegram entry.

    Returns:
        - 200: Telegram entry details.
        - 404: Telegram entry not found.
        - 400: Invalid telegram_id format.
        - 500: Internal server error.
    """
    logger.info(f"Fetching Telegram entry with ID: {telegram_id}")

    # Validate telegram_id format
    try:
        telegram_id = str(UUID(telegram_id))  # Convert UUID to string for psycopg2
    except ValueError:
        logger.error("Invalid telegram_id format.")
        return jsonify({"message": "Invalid telegram_id format."}), 400

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT telegram_id, telegram_account_id, telegram_user_id, telegram_username, telegram_verified, telegram_is_admin, telegram_created "
                "FROM telegram WHERE telegram_id = %s",
                (telegram_id,)
            )
            result = cursor.fetchone()

            if not result:
                logger.warning(f"No Telegram entry found with ID: {telegram_id}.")
                return jsonify({"message": "Telegram entry not found."}), 404

            logger.info(f"Telegram entry with ID: {telegram_id} retrieved successfully.")
            return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error fetching Telegram entry with ID: {telegram_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500



@telegram_bp.route('/account/<account_id>', methods=['GET'])
def get_telegram_by_account(account_id):
    """
    Retrieve a Telegram entry by the associated account_id.

    Args:
        account_id (UUID): The ID of the user account.

    Returns:
        - 200: Telegram entry details.
        - 404: Telegram entry not found for the given account.
        - 400: Invalid account_id format.
        - 500: Internal server error.
    """
    logger.info(f"Fetching Telegram entry for account ID: {account_id}")

    # Validate account_id format
    try:
        account_id = str(UUID(account_id))  # Convert UUID to string for psycopg2
    except ValueError:
        logger.error("Invalid account_id format.")
        return jsonify({"message": "Invalid account_id format."}), 400

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT telegram_id, telegram_account_id, telegram_user_id, telegram_username, telegram_verified, telegram_is_admin, telegram_created "
                "FROM telegram WHERE telegram_account_id = %s",
                (account_id,)
            )
            result = cursor.fetchone()

            if not result:
                logger.warning(f"No Telegram entry found for account ID: {account_id}.")
                return jsonify({"message": "Telegram entry not found for the given account."}), 404

            logger.info(f"Telegram entry for account ID: {account_id} retrieved successfully.")
            return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error fetching Telegram entry for account ID: {account_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500




@telegram_bp.route('/<telegram_id>/admin', methods=['PUT'])
def update_telegram_verified_and_admin(telegram_id):
    """
    Update the 'telegram_verified' and 'admin' fields of an existing Telegram entry.

    Request JSON format:
    {
        "telegram_is_admin": "boolean"
    }

    Returns:
        - 200: Successfully updated.
        - 400: Invalid input or missing required fields.
        - 404: Telegram entry not found.
        - 500: Internal server error.
    """
    data = request.json
    logger.info(f"Updating Telegram entry with ID: {telegram_id}")

    # Validate telegram_id format
    try:
        telegram_id = str(UUID(telegram_id))  # Convert UUID to string for psycopg2
    except ValueError:
        logger.error("Invalid telegram_id format.")
        return jsonify({"message": "Invalid telegram_id format."}), 400

    # Ensure at least one of the fields to update is provided
    if 'telegram_is_admin' not in data:
        logger.warning("Missing field to update.")
        return jsonify({"message": "No fields to update. Provide 'telegram_is_admin'."}), 400

    telegram_is_admin = data.get('telegram_is_admin')

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE telegram SET telegram_is_admin = %s WHERE telegram_id = %s RETURNING telegram_id",
                (telegram_is_admin, telegram_id)
            )
            updated_id = cursor.fetchone()

            if not updated_id:
                logger.warning(f"Telegram entry with ID: {telegram_id} not found.")
                return jsonify({"message": "Telegram entry not found."}), 404

            conn.commit()  # Commit the transaction
            logger.info(f"Telegram entry with ID: {telegram_id} successfully updated.")
            return jsonify({"message": "Telegram entry updated successfully", "telegram_id": telegram_id}), 200

    except Exception as e:
        logger.error(f"Error updating Telegram entry with ID: {telegram_id}: {str(e)}")
        conn.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500



@telegram_bp.route('/<telegram_id>/verified', methods=['PUT'])
def update_telegram_verified(telegram_id):
    """
    Update the 'telegram_verified' field of an existing Telegram entry.

    Request JSON format:
    {
        "telegram_verified": "boolean"
    }

    Returns:
        - 200: Successfully updated.
        - 400: Invalid input or missing required fields.
        - 404: Telegram entry not found.
        - 500: Internal server error.
    """
    data = request.json
    logger.info(f"Updating 'telegram_verified' for Telegram entry with ID: {telegram_id}")

    # Validate telegram_id format
    try:
        telegram_id = str(UUID(telegram_id))  # Convert UUID to string for psycopg2
    except ValueError:
        logger.error("Invalid telegram_id format.")
        return jsonify({"message": "Invalid telegram_id format."}), 400

    # Check if the 'telegram_verified' field is present in the request
    if 'telegram_verified' not in data:
        logger.warning("Missing 'telegram_verified' field in request.")
        return jsonify({"message": "Missing 'telegram_verified' field."}), 400

    telegram_verified = data.get('telegram_verified')

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE telegram SET telegram_verified = %s WHERE telegram_id = %s RETURNING telegram_id",
                (telegram_verified, telegram_id)
            )
            updated_id = cursor.fetchone()

            if not updated_id:
                logger.warning(f"Telegram entry with ID: {telegram_id} not found.")
                return jsonify({"message": "Telegram entry not found."}), 404

            conn.commit()  # Commit the transaction
            logger.info(f"'telegram_verified' for entry ID: {telegram_id} successfully updated.")
            return jsonify({"message": "'telegram_verified' updated successfully", "telegram_id": telegram_id}), 200

    except Exception as e:
        logger.error(f"Error updating 'telegram_verified' for entry ID: {telegram_id}: {str(e)}")
        conn.rollback()  # Rollback the transaction on error
        return jsonify({"error": str(e)}), 500



@telegram_bp.route('/<telegram_id>', methods=['DELETE'])
def delete_telegram(telegram_id):
    """
        Delete a Telegram entry by its ID.

        Args:
            telegram_id (UUID): The ID of the Telegram entry to be deleted.

        Returns:
            - 200: Successfully deleted the Telegram entry.
            - 404: Telegram entry not found for the given ID.
            - 500: Internal server error if an exception occurs during the deletion process.
    """
    logger.info(f"Deleting Telegram entry with ID: {telegram_id}")

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM telegram WHERE telegram_id = %s",
                (telegram_id,)
            )
            if cursor.rowcount == 0:
                logger.warning(f"No Telegram entry found with ID: {telegram_id}.")
                return jsonify({"message": "Telegram entry not found."}), 404

            conn.commit()  # Commit the transaction
            logger.info(f"Successfully deleted Telegram entry with ID: {telegram_id}.")
            return jsonify({"message": "Successfully deleted Telegram entry."}), 200

    except Exception as e:
        logger.error(f"Error deleting Telegram entry with ID: {telegram_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500



@telegram_bp.route('/search', methods=['GET'])
def search_telegram_entries():
    """
    Search for Telegram entries based on provided query parameters.

    Query Parameters:
        - username (str): Filter by Telegram username.
        - verified (bool): Filter by verification status (true or false).
        - is_admin (bool): Filter by admin status (true or false).

    Returns:
        - 200: List of matching Telegram entries.
        - 400: Invalid query parameter format.
        - 500: Internal server error if an exception occurs during the search process.

    Example Request:
        GET /telegram/search?username=Monster&verified=true&is_admin=false

    Example Response (Success):
        [
            {
                "telegram_id": "e5845f2a-a5c2-4126-93eb-6625114a2b42",
                "telegram_account_id": "58ad78c4-b13f-4cca-978e-cea672879a15",
                "telegram_user_id": "tssss2e1",
                "telegram_username": "Monster14",
                "telegram_verified": true,
                "telegram_created": "2024-10-17T16:44:05Z",
                "telegram_is_admin": false
            }
        ]

    Example Response (Error):
        {
            "error": "Error message here"
        }
    """
    username = request.args.get('username')
    verified = request.args.get('verified')
    is_admin = request.args.get('is_admin')

    query = "SELECT telegram_id, telegram_account_id, telegram_user_id, telegram_username, telegram_verified, telegram_created FROM telegram WHERE TRUE"
    filters = []

    if username:
        query += " AND telegram_username ILIKE %s"
        filters.append(f"%{username}%")  # Allow partial matches

    if verified is not None:
        try:
            verified = bool(verified.lower() == 'true')
            query += " AND telegram_verified = %s"
            filters.append(verified)
        except ValueError:
            return jsonify({"message": "Invalid verified parameter format."}), 400

    if is_admin is not None:
        try:
            is_admin = bool(is_admin.lower() == 'true')
            query += " AND telegram_is_admin = %s"
            filters.append(is_admin)
        except ValueError:
            return jsonify({"message": "Invalid is_admin parameter format."}), 400

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, filters)
            results = cursor.fetchall()

            return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error searching Telegram entries: {str(e)}")
        return jsonify({"error": str(e)}), 500

