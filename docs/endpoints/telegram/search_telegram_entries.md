#### Responses:

- **200**: Successfully deleted the Telegram entry.
    - Example:
      ```json
      {
        "message": "Successfully deleted Telegram entry."
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
This endpoint allows you to delete a Telegram entry by its unique `telegram_id`.

- If the specified Telegram entry is not found, a `404` error will be returned.
- If there is an internal server error during the deletion process, a `500` error will be returned.
- The operation will commit the deletion to the database if successful.

### Request

#### URL Parameters

| Parameter     | Type   | Required | Description                      |
|---------------|--------|----------|----------------------------------|
| telegram_id   | UUID   | Yes      | The unique identifier of the Telegram entry |

### Example

#### Request

```http
DELETE /<telegram_id> HTTP/1.1
