# Link Telegram Account Endpoint

Links a Telegram account to an existing user account.

## Endpoint

**POST /link**

## Description

This endpoint creates a new Telegram entry in the database associated with a user account. It verifies required fields, handles potential conflicts (such as duplicate Telegram user IDs or usernames), and ensures that the account exists before linking the Telegram account. It also manages optional fields like Telegram username and verification status.

## Request

### Headers

- Content-Type: application/json

### Body

```json
{
    "telegram_account_id": "UUID",       # The ID of the user account from the 'account' table (must be a valid UUID).
    "telegram_user_id": "string",        # Unique identifier for the Telegram user (required).
    "telegram_username": "string",       # Unique Telegram username (optional).
    "telegram_verified": "boolean",      # Whether the Telegram account is verified (default is False if not provided).
    "telegram_is_admin": "boolean"       # Whether the Telegram account has admin privileges (optional).
}
```

### Fields

| Field              | Type    | Required | Description                                                                 |
|--------------------|---------|----------|-----------------------------------------------------------------------------|
| telegram_account_id | UUID    | Yes      | The ID of the user account to which the Telegram account will be linked.     |
| telegram_user_id    | string  | Yes      | The unique identifier for the Telegram user.                                |
| telegram_username   | string  | No       | The Telegram username (optional).                                           |
| telegram_verified   | boolean | No       | Whether the Telegram account is verified (defaults to False).               |
| telegram_is_admin   | boolean | No       | Whether the Telegram account has admin privileges.                          |

## Response

### Success Response

- **Code:** 201 Created
- **Content:**
  
```json
{
    "message": "Telegram entry created successfully",
    "telegram_username": "string"  # The Telegram username associated with the entry.
}
```

### Error Responses

- **Code:** 400 Bad Request
  - **Content:** { "message": "Missing required fields: telegram_account_id or telegram_user_id." }
  - **Content:** { "message": "Invalid telegram_account_id format." }
  - **Content:** { "message": "The provided data violates a check constraint." }

- **Code:** 404 Not Found
  - **Content:** { "message": "Account not found. Please ensure the account exists before linking a Telegram." }

- **Code:** 409 Conflict
  - **Content:** { "message": "A Telegram entry with this user ID already exists." }
  - **Content:** { "message": "A Telegram entry with this username already exists." }
  - **Content:** { "message": "A Telegram entry with these details already exists." }

- **Code:** 500 Internal Server Error
  - **Content:** { "message": "A database error occurred.", "error": "detailed_error_message" }

## Notes

- The `telegram_account_id` must be a valid UUID referencing an existing account in the system.
- The `telegram_user_id` must be unique across all Telegram entries.
- The `telegram_username` is optional but must also be unique if provided.
- If the `telegram_verified` field is not provided, it defaults to `False`.
- If the `telegram_is_admin` field is not provided, it defaults to `False`.

## Example

### Request

```http
POST /link HTTP/1.1
Content-Type: application/json

{
    "telegram_account_id": "123e4567-e89b-12d3-a456-426614174000",
    "telegram_user_id": "user1234",
    "telegram_username": "john_doe",
    "telegram_verified": true,
    "telegram_is_admin": false
}
```

### Success Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "message": "Telegram entry created successfully",
    "telegram_username": "john_doe"
}
```

### Error Response (Missing Field)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "message": "Missing required fields: telegram_account_id"
}
```

### Error Response (Account Not Found)

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
    "message": "Account not found. Please ensure the account exists before linking a Telegram."
}
```
