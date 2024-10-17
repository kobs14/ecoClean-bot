# Get Account by ID Endpoint

Retrieves a specific account and its associated emails and Telegram info by account ID.

## Endpoint

`GET account/<id>`

## Description

This endpoint fetches an account from the database using the provided account ID. It returns comprehensive account details along with any associated email addresses and Telegram information.

## Request

### Parameters

- `id` (path parameter): The unique identifier of the account (UUID format).

### Headers

No specific headers required.

## Response

### Success Response

- **Code:** 200 OK
- **Content:** A JSON object with the following structure:

```json
{
  "account_id": "string (UUID)",
  "account_username": "string",
  "account_fullname": "string",
  "account_phone": "string",
  "account_is_admin": boolean,
  "account_commission_rate": number,
  "account_status": "string",
  "emails": [
    {
      "email_id": number,
      "email_address": "string",
      "email_account_id": "string (UUID)"
    }
  ],
  "telegram": {
    "telegram_id": number,
    "telegram_username": "string",
    "telegram_account_id": "string (UUID)"
  }
}
```

### Error Responses

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Invalid account ID format" }`
  - **Description:** When the provided ID is not in a valid UUID format.

- **Code:** 404 Not Found
  - **Content:** `{ "message": "Account not found" }`
  - **Description:** When no account matches the provided ID.

- **Code:** 500 Internal Server Error
  - **Content:** `{ "error": "Error message description" }`
  - **Description:** When an unexpected error occurs during the process.

## Notes

- The account ID must be in a valid UUID format.
- The response includes all details of the account, including any associated email addresses and Telegram information.
- If the account has no associated emails, the `emails` field will be an empty array.
- If the account has no associated Telegram info, the `telegram` field will be `null`.

## Example

### Request

```http
GET /123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Host: your-api-domain.com
```

### Success Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "account_username": "johndoe",
  "account_fullname": "John Doe",
  "account_phone": "+1234567890",
  "account_is_admin": false,
  "account_commission_rate": 0.05,
  "account_status": "active",
  "emails": [
    {
      "email_id": 1,
      "email_address": "john@example.com",
      "email_account_id": "123e4567-e89b-12d3-a456-426614174000"
    },
    {
      "email_id": 2,
      "email_address": "doe@example.com",
      "email_account_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  ],
  "telegram": {
    "telegram_id": 1,
    "telegram_username": "johndoe_telegram",
    "telegram_account_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

### Error Response (Invalid ID)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "message": "Invalid account ID format"
}
```

### Error Response (Not Found)

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "message": "Account not found"
}
```