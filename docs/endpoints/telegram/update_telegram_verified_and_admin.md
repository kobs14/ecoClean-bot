
## PUT /<telegram_id>/admin

### Update the 'telegram_verified' and 'admin' fields of an existing Telegram entry.

#### Request Body (JSON):
```json
{
  "telegram_is_admin": "boolean"  # (Required) Whether the Telegram user is an admin (true or false)
}
```

#### Responses:

- **200**: Successfully updated.
    - Example:
      ```json
      {
        "message": "Telegram entry updated successfully",
        "telegram_id": "UUID"
      }
      ```

- **400**: Invalid input or missing required fields.
    - Example:
      ```json
      {
        "message": "Invalid type for telegram_is_admin. Expected a boolean."
      }
      ```

- **404**: Telegram entry not found for the given `telegram_id`.
    - Example:
      ```json
      {
        "message": "Telegram entry not found."
      }
      ```

- **500**: Internal server error.
    - Example:
      ```json
      {
        "error": "Detailed error message describing the problem"
      }
      ```

### Description:
This endpoint allows you to update the `telegram_is_admin` field of an existing Telegram entry, marking the user as an admin. The `telegram_verified` field is not updated in this operation.

- The request body must contain the `telegram_is_admin` field as a boolean.
- If no fields to update are provided, or if the provided data is invalid, an error will be returned.
- The system will ensure the `telegram_id` format is valid before proceeding.
- If the specified Telegram entry is not found, a `404` error will be returned.
