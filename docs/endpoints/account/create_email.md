# Create Email Endpoint

Creates a new email address associated with an existing account.

## Endpoint

`POST /email`

## Description

This endpoint receives an account ID and an email address, validates the input, and creates a new email entry in the database associated with the specified account.

## Request

### Headers

- Content-Type: application/json

### Body

A JSON object containing the following fields:

```json
{
  "account_id": "UUID",
  "email": "string"
}
```

## Response

### Success Response

- **Code:** 201 Created
- **Content:** 
```json
{
  "message": "Email created successfully",
  "email_id": "integer"
}
```

### Error Responses

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Missing required fields: account_id or email." }`
  - **Description:** When either account_id or email is not provided in the request.

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Invalid account ID format" }`
  - **Description:** When the provided account_id is not a valid UUID.

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Invalid email format." }`
  - **Description:** When the provided email address is not in a valid format.

- **Code:** 404 Not Found
  - **Content:** `{ "message": "Account not found." }`
  - **Description:** When no account matches the provided account_id.

- **Code:** 409 Conflict
  - **Content:** `{ "message": "Email already exists." }`
  - **Description:** When the provided email address is already associated with an account.

- **Code:** 500 Internal Server Error
  - **Content:** `{ "error": "Error message description" }`
  - **Description:** When an unexpected error occurs during the process.

## Notes

- The account_id must be a valid UUID and must correspond to an existing account in the system.
- The email address must be in a valid format and must be unique in the system.
- If the email is successfully created, the response includes the newly created email_id.

## Example

### Request

```http
POST /email HTTP/1.1
Host: your-api-domain.com
Content-Type: application/json

{
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com"
}
```

### Success Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "message": "Email created successfully",
  "email_id": 1234
}
```

### Error Response (Invalid Email)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "message": "Invalid email format."
}
```

### Error Response (Email Exists)

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "message": "Email already exists."
}
```