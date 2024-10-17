# Update Account Endpoint

Updates specific fields of an account identified by its UUID.

## Endpoint

`PATCH /<id>`

## Description

This endpoint allows clients to update one or more fields of an existing account. Only the fields provided in the request body will be updated. If a field is not included in the request, it will remain unchanged.

## Request

### Parameters

- `id` (path parameter): The UUID of the account to be updated.

### Headers

- Content-Type: application/json

### Body

A JSON object containing the fields to be updated. Valid fields are:

- `username` (string)
- `fullname` (string)
- `phone` (string)
- `password` (string)
- `is_admin` (boolean)
- `commission_rate` (number)
- `status` (string)

Example:

```json
{
  "username": "new_username",
  "phone": "+1234567890"
}
```

## Response

### Success Response

- **Code:** 200 OK
- **Content:** 
```json
{
  "message": "Account updated successfully"
}
```

### Error Responses

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Invalid account ID format" }`
  - **Description:** When the provided ID is not in a valid UUID format.

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "No valid fields to update" }`
  - **Description:** When no valid fields are provided in the request body.

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Invalid value for [field]: [error message]" }`
  - **Description:** When a provided field value is invalid.

- **Code:** 404 Not Found
  - **Content:** `{ "message": "Account not found" }`
  - **Description:** When no account matches the provided ID.

- **Code:** 409 Conflict
  - **Content:** `{ "message": "Username already exists." }`
  - **Description:** When trying to update to a username that already exists.

- **Code:** 409 Conflict
  - **Content:** `{ "message": "Phone number already exists." }`
  - **Description:** When trying to update to a phone number that already exists.

- **Code:** 500 Internal Server Error
  - **Content:** `{ "error": "Error message description" }`
  - **Description:** When an unexpected error occurs during the process.

## Notes

- The account ID must be in a valid UUID format.
- Only the fields provided in the request body will be updated.
- The password, if provided, will be automatically hashed before storage.
- The `account_updated_at` timestamp is automatically updated when any field is changed.
- Unique constraints are enforced on username and phone number.

## Example

### Request

```http
PATCH /123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Host: your-api-domain.com
Content-Type: application/json

{
  "username": "new_username",
  "phone": "+1234567890",
  "is_admin": true
}
```

### Success Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Account updated successfully"
}
```

### Error Response (Invalid Field Value)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "message": "Invalid value for phone: Invalid phone number format"
}
```

### Error Response (Conflict)

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "message": "Username already exists."
}
```