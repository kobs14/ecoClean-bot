# Delete Account Endpoint

Deletes an account and all associated records from the system.

## Endpoint

`DELETE /<id>`

## Description

This endpoint removes the specified account from the system along with any associated records in the Telegram and email tables. The deletion of associated Telegram records is handled automatically due to the ON DELETE CASCADE constraint.

## Request

### Parameters

- `id` (path parameter): The UUID of the account to be deleted.

### Headers

No specific headers required.

## Response

### Success Response

- **Code:** 200 OK
- **Content:** 
```json
{
  "message": "Account and associated records deleted successfully"
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
  - **Description:** When an unexpected error occurs during the deletion process.

## Notes

- The account ID must be in a valid UUID format.
- This operation is irreversible. All data associated with the account will be permanently deleted.
- The deletion process includes:
  1. Deleting associated Telegram records (handled by ON DELETE CASCADE)
  2. Deleting associated email records
  3. Deleting the account itself
- If the account doesn't exist, a 404 error is returned before any deletion attempt.

## Example

### Request

```http
DELETE /123e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Host: your-api-domain.com
```

### Success Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Account and associated records deleted successfully"
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