## GET /<telegram_id>

### Retrieve a Telegram entry by its `telegram_id`.

#### Args:
- `telegram_id` (UUID): The unique ID of the Telegram entry.

#### Responses:

- **200**: Telegram entry details returned successfully.
    - Example:
      ```json
      {
        "telegram_id": "UUID",
        "telegram_account_id": "UUID",
        "telegram_user_id": "string",
        "telegram_username": "string",
        "telegram_verified": true,
        "telegram_is_admin": false,
        "telegram_created": "timestamp"
      }
      ```

- **404**: Telegram entry not found.
    - Example:
      ```json
      {
        "message": "Telegram entry not found."
      }
      ```

- **400**: Invalid `telegram_id` format.
    - Example:
      ```json
      {
        "message": "Invalid telegram_id format."
      }
      ```

- **500**: Internal server error.
    - Example:
      ```json
      {
        "error": "Detailed error message describing the problem."
      }
      ```

### Description:
This endpoint allows you to retrieve the details of a Telegram entry by providing its unique `telegram_id`. If the entry is found, the details will be returned in the response. If the `telegram_id` format is invalid, or if no entry is found, the appropriate error message will be returned.
