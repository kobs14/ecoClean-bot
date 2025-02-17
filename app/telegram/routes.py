
from uuid import UUID
import psycopg2
from flask import Blueprint, jsonify, request

from app.auth.decorators import requires_role
from app.main import global_conn as conn
from app.config import logger

telegram_bp = Blueprint('telegram', __name__)

@telegram_bp.route('/link', methods=['POST'])
def link_telegram_account():
    """
    Link and verify a Telegram account using a verification token.

    Request JSON format:
    {
        "telegram_user_id": "string",        # Unique identifier for the Telegram user (required).
        "telegram_username": "string",       # Unique Telegram username (required).
        "verification_token": "UUID"         # Verification token from the welcome email (required).
    }

    Responses:
        - 200: Telegram account linked and verified successfully.
        - 400: Bad request due to missing required fields or invalid data format.
        - 404: Verification token not found or expired.
        - 409: Conflict due to unique constraint violation (e.g., duplicate user ID or username).
        - 500: Internal server error.
    """
    data = request.json
    logger.info(f"Attempting to link Telegram account with data: {data}")

    # Validate required fields
    required_fields = ['telegram_user_id', 'verification_token', 'telegram_username']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
        return jsonify({"message": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    telegram_user_id = data['telegram_user_id']
    telegram_username = data.get('telegram_username')
    verification_token = data['verification_token']

    try:
        with conn.cursor() as cursor:
            # Find the Telegram entry with the verification token
            cursor.execute(
                "SELECT telegram_id, telegram_account_id FROM telegram WHERE telegram_verification_token = %s",
                (verification_token,)
            )
            result = cursor.fetchone()

            if not result:
                logger.error(f"Verification token not found: {verification_token}")
                return jsonify({"message": "Verification token not found or expired."}), 404

            telegram_account_id = result['telegram_account_id']

            # Update the Telegram entry with the user ID, username, and mark as verified
            cursor.execute(
                """UPDATE telegram 
                   SET telegram_id = %s, telegram_username = %s, telegram_verified = TRUE 
                   WHERE telegram_account_id = %s""",
                (telegram_user_id, telegram_username, telegram_account_id)
            )

            conn.commit()  # Commit the transaction

        logger.info(f"Telegram account linked and verified successfully for account ID: {telegram_account_id}")
        return jsonify({"message": "Telegram account linked and verified successfully"}), 200

    except psycopg2.errors.UniqueViolation as e:
        if "telegram_user_id_key" in str(e):
            return jsonify({"message": "A Telegram entry with this user ID already exists."}), 409
        elif "telegram_username_key" in str(e):
            return jsonify({"message": "A Telegram entry with this username already exists."}), 409
        else:
            return jsonify({"message": "A unique constraint violation occurred."}), 409

    except psycopg2.errors.ForeignKeyViolation:
        return jsonify({"message": "Account not found. Please ensure the account exists before linking a Telegram."}), 404

    except psycopg2.errors.CheckViolation:
        return jsonify({"message": "The provided data violates a check constraint."}), 400

    except Exception as e:
        logger.error(f"Unexpected error linking Telegram account: {str(e)}")
        conn.rollback()
        return jsonify({"error": "An unexpected error occurred."}), 500


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
                "SELECT telegram_id, telegram_account_id, telegram_username, telegram_verified, telegram_is_admin, telegram_created "
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
                "SELECT telegram_id, telegram_account_id, telegram_username, telegram_verified, telegram_is_admin, telegram_created "
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



@requires_role("admin")
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

    # Validate telegram_is_admin is a boolean
    telegram_is_admin = data.get('telegram_is_admin')
    if not isinstance(telegram_is_admin, bool):
        logger.warning(f"Invalid type for telegram_is_admin: {type(telegram_is_admin)}")
        return jsonify({"message": "Invalid type for telegram_is_admin. Expected a boolean."}), 400

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE telegram SET telegram_is_admin = %s WHERE telegram_id = %s RETURNING telegram_id",
                (telegram_is_admin, telegram_id))
            updated_id = cursor.fetchone()

            if not updated_id:
                logger.warning(f"Telegram entry with ID: {telegram_id} not found.")
                return jsonify({"error": "Telegram entry not found."}), 404

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
        - telegram_username (str): Filter by Telegram username.
        - telegram_verified (bool): Filter by verification status (true or false).
        - is_admin (bool): Filter by admin status (true or false).

    Returns:
        - 200: List of matching Telegram entries.
        - 400: Invalid query parameter format.
        - 500: Internal server error if an exception occurs during the search process.
    """
    username = request.args.get('telegram_username')
    verified = request.args.get('telegram_verified')
    is_admin = request.args.get('telegram_is_admin')

    # Validate verified parameter
    if verified is not None:
        if verified.lower() not in ['true', 'false']:
            logger.warning(f"Invalid verified parameter: {verified}")
            return jsonify({"message": "Invalid verified parameter format. Expected 'true' or 'false'."}), 400
        verified = verified.lower() == 'true'

    # Validate is_admin parameter
    if is_admin is not None:
        if is_admin.lower() not in ['true', 'false']:
            logger.warning(f"Invalid is_admin parameter: {is_admin}")
            return jsonify({"message": "Invalid is_admin parameter format. Expected 'true' or 'false'."}), 400
        is_admin = is_admin.lower() == 'true'

    # Construct the query
    query = "SELECT telegram_id, telegram_account_id, telegram_user_id, telegram_username, telegram_verified, telegram_created FROM telegram WHERE TRUE"
    filters = []

    if username:
        query += " AND telegram_username ILIKE %s"
        filters.append(f"%{username}%")  # Allow partial matches

    if verified is not None:
        query += " AND telegram_verified = %s"
        filters.append(verified)

    if is_admin is not None:
        query += " AND telegram_is_admin = %s"
        filters.append(is_admin)

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, filters)
            results = cursor.fetchall()

            return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error searching Telegram entries: {str(e)}")
        return jsonify({"error": str(e)}), 500