import uuid
from typing import Optional, Tuple


def is_valid_uuid(val):
    """Check if string is a valid UUID"""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def validate_account(
        account_id: Optional[str] = None,
        account_fullname: Optional[str] = None,
        db_connection=None
) -> Tuple[bool, Optional[str]]:
    """
    Validate account parameters
    Returns (is_valid, error_message)
    """
    if not account_id and not account_fullname:
        return True, None

    try:
        if account_id:
            if not is_valid_uuid(account_id):
                return False, "Invalid account ID format. Must be a valid UUID."

            # Check if account exists and is active
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM account 
                    WHERE account_id = %s 
                    AND account_status = 'active'
                )
            """
            with db_connection.cursor() as cur:
                cur.execute(query, (account_id,))
                exists = cur.fetchone()[0]
                if not exists:
                    return False, f"Account with ID {account_id} not found or is inactive."

        if account_fullname:
            # Check if account exists and is active
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM account 
                    WHERE LOWER(account_fullname) LIKE LOWER(%s)
                    AND account_status = 'active'
                )
            """
            with db_connection.cursor() as cur:
                cur.execute(query, (f"%{account_fullname}%",))
                exists = cur.fetchone()[0]
                if not exists:
                    return False, f"No active accounts found matching name '{account_fullname}'."

        return True, None

    except Exception as e:
        return False, f"Error validating account: {str(e)}"
