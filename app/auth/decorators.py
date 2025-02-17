
from functools import wraps
from uuid import UUID
from app.config import logger
from flask import request, jsonify
from app.main import global_conn as conn
from psycopg2.extras import RealDictCursor

def validate_uuid(uuid_str):
    """
    Validate if the input string is a valid UUID.
    """
    try:
        return UUID(uuid_str)  # This will raise ValueError if the UUID is invalid
    except ValueError:
        return None

def get_current_user():
    """
    Retrieve the current authenticated user from the database.
    This function validates the UUID in the headers before querying the database.
    """
    user_account_id = request.headers.get('account_id')
    if not user_account_id:
        logger.warning("No account_id provided in headers.")
        return None

    # Validate the account_id UUID format
    if not validate_uuid(user_account_id):
        logger.error(f"Invalid account_id UUID format: {user_account_id}")
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM account WHERE account_id = %s", (user_account_id,))
            user = cursor.fetchone()
            if not user:
                logger.warning(f"User with account_id {user_account_id} not found.")
            return user
    except Exception as e:
        logger.error(f"Error fetching user from database: {str(e)}")
        return None

def requires_role(role):
    """
    Decorator to enforce role-based access control with UUID validation.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get the current authenticated user
            user = get_current_user()
            if not user:
                return jsonify({"message": "Unauthorized: Invalid or missing account_id"}), 401

            # Check if the user has the required role
            if role == "admin" and not user.get("account_is_admin"):
                return jsonify({"message": "Forbidden: Admin access required"}), 403

            # If the user has the required role, proceed
            return f(*args, **kwargs)
        return wrapped
    return decorator