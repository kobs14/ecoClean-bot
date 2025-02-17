# Get All Accounts Endpoint

Retrieves all accounts from the database, including related email and Telegram details.

## Endpoint

`GET /all`

## Description

This endpoint fetches all accounts from the database, performing a LEFT JOIN between the account, email, and telegram tables. It retrieves comprehensive account details along with any associated email addresses and Telegram information. The accounts are ordered by admin status (admins first) and then by full name in ascending order.

## Request

### Headers

No specific headers required.

## Response

### Success Response

- **Code:** 200 OK
- **Content:** A JSON array of account objects. Each account object has the following structure:

```json
[
  {
    "account": {
      "account_id": number,
      "account_username": "string",
      "account_fullname": "string",
      "account_phone": "string",
      "account_is_admin": boolean,
      "account_commission_rate": number,
      "account_status": "string"
      // ... other account fields
    },
    "emails": [
      {
        "email_id": number,
        "email_address": "string",
        "email_account_id": number
        // ... other email fields
      }
      // ... potentially multiple email objects
    ],
    "telegram": {
      "telegram_id": number,
      "telegram_username": "string",
      "telegram_account_id": number
      // ... other telegram fields
    }
  }
  // ... multiple account objects
]
```

### Error Response

- **Code:** 500 Internal Server Error
- **Content:** 
```json
{
  "error": "Error message description"
}
```

## Notes

- The response includes all accounts, regardless of their status.
- Email and Telegram information is included if available. If an account has no associated email or Telegram data, these fields will be an empty array or null respectively.
- Accounts are ordered with admin accounts first, followed by non-admin accounts. Within each group, accounts are sorted alphabetically by full name.

## Example

### Request

```http
GET /all HTTP/1.1
Host: your-api-domain.com
```

### Success Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "account": {
      "account_id": 1,
      "account_username": "admin_user",
      "account_fullname": "Admin User",
      "account_phone": "+1234567890",
      "account_is_admin": true,
      "account_commission_rate": 0.1,
      "account_status": "active"
    },
    "emails": [
      {
        "email_id": 1,
        "email_address": "admin@example.com",
        "email_account_id": 1
      }
    ],
    "telegram": {
      "telegram_id": 1,
      "telegram_username": "admin_telegram",
      "telegram_account_id": 1
    }
  },
  {
    "account": {
      "account_id": 2,
      "account_username": "regular_user",
      "account_fullname": "Regular User",
      "account_phone": "+9876543210",
      "account_is_admin": false,
      "account_commission_rate": 0.05,
      "account_status": "active"
    },
    "emails": [
      {
        "email_id": 2,
        "email_address": "user@example.com",
        "email_account_id": 2
      }
    ],
    "telegram": null
  }
]
```

### Error Response

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Database connection error"
}
```