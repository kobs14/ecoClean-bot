# Database Schema Documentation

## Table: `account`

This table stores the details of each account in the system.

| Column                      | Type           | Constraints                               |
|-----------------------------|----------------|-------------------------------------------|
| `account_id`                | UUID           | Primary key, default: `gen_random_uuid()` |
| `account_username`          | VARCHAR(255)   | Not null, unique                          |
| `account_fullname`          | VARCHAR(255)   | Not null                                  |
| `account_phone`             | VARCHAR(20)    | Not null, unique                          |
| `account_password_hash`     | VARCHAR(255)   | Not null                                  |
| `account_forgot_token_hash` | VARCHAR(255)   | Nullable                                  |
| `account_forgot_requested`  | TIMESTAMP      | Nullable                                  |
| `account_last_login`        | TIMESTAMP      | Nullable                                  |
| `account_is_admin`          | BOOLEAN        | Not null, default: `false`                |
| `account_commission_rate`   | DECIMAL(5, 2)  | Must be between 0 and 100                 |
| `account_status`            | VARCHAR(64)    | Not null, values: `active`, `disabled`    |
| `account_created`           | TIMESTAMP      | Not null, default: `CURRENT_TIMESTAMP`    |
| `account_updated_at`        | TIMESTAMP      | Default: `CURRENT_TIMESTAMP`              |

## Table: `email`

This table stores email addresses linked to accounts.

| Column             | Type           | Constraints                                                                  |
|--------------------|----------------|------------------------------------------------------------------------------|
| `email_id`         | UUID           | Primary key, default: `gen_random_uuid()`                                    |
| `email_account_id` | UUID           | Foreign key referencing `account(account_id)` on delete `RESTRICT`, not null |
| `email_address`    | VARCHAR(255)   | Not null, unique                                                             |
| `email_created`    | TIMESTAMP      | Not null, default: `CURRENT_TIMESTAMP`                                       |
| `email_verified`   | TIMESTAMP      | Nullable                                                                     |
| `email_verification_token` | UUID           | Nullable                                                                     |

## Table: `telegram`

This table stores the Telegram account details linked to an account.

| Column                | Type            | Constraints                                                                 |
|-----------------------|-----------------|-----------------------------------------------------------------------------|
| `telegram_id`         | UUID            | Primary key, default: `gen_random_uuid()`                                   |
| `telegram_account_id` | UUID            | Foreign key referencing `account(account_id)` on delete `CASCADE`, not null |
| `telegram_username`   | VARCHAR(255)    | Unique                                                                      |
| `telegram_verification_token`   | UUID    | Nullable                                                                      |
| `telegram_verified`   | BOOLEAN         | Not null, default: `false`                                                  |
| `telegram_is_admin`   | BOOLEAN         | Not null, default: `false`                                                  |
| `telegram_created`    | TIMESTAMP       | Not null, default: `CURRENT_TIMESTAMP`                                      |

## Table: `job_report`

This table stores job reports submitted by employees.

| Column                    | Type             | Constraints                                                                              |
|---------------------------|------------------|------------------------------------------------------------------------------------------|
| `job_report_id`           | UUID             | Primary key, default: `gen_random_uuid()`                                                |
| `report_by_account_id`    | UUID             | Foreign key referencing `account(account_id)` on delete `RESTRICT`                       |
| `latitude`                | DECIMAL(10, 8)   | Nullable                                                                                 |
| `longitude`               | DECIMAL(11, 8)   | Nullable                                                                                 |
| `created_at`              | TIMESTAMP        | Default: `CURRENT_TIMESTAMP`                                                             |
| `amount_received_dollars` | DECIMAL(10, 2)   | Not null                                                                                 |
| `payment_method`          | ENUM             | Values: `Cash`, `Check`, `Card`, `Venmo`, `PayPal`, `CashApp`, `Bank Transfer`, `Other`  |
| `job_description`         | TEXT             | Nullable                                                                                 |
| `client_name`             | VARCHAR(255)     | Nullable                                                                                 |
| `client_contact`          | VARCHAR(255)     | Nullable                                                                                 |
| `job_status`              | VARCHAR(50)      | Default: `completed`, values: `pending`, `in_progress`, `completed`, `cancelled`         |
| `notes`                   | TEXT             | Nullable                                                                                 |
| `updated_at`              | TIMESTAMP        | Default: `CURRENT_TIMESTAMP`                                                             |

## Table: `report_photos`

This table stores photos related to job reports.

| Column                | Type           | Constraints                                                                       |
|-----------------------|----------------|-----------------------------------------------------------------------------------|
| `photo_id`            | UUID           | Primary key, default: `gen_random_uuid()`                                         |
| `photo_job_report_id` | UUID           | Foreign key referencing `job_report(job_report_id)` on delete `CASCADE`, not null |
| `photo_url`           | VARCHAR(255)   | Not null                                                                          |
| `file_name`           | VARCHAR(255)   | Not null                                                                          |
| `file_size`           | INTEGER        | Not null                                                                          |
| `created_at`          | TIMESTAMP      | Default: `CURRENT_TIMESTAMP`                                                      |

## Type: `payment_method_enum`

An enum type that defines possible payment methods for job reports.

| Value              |
|--------------------|
| `Cash`             |
| `Check`            |
| `Card`             |
| `Venmo`            |
| `PayPal`           |
| `CashApp`          |
| `Bank Transfer`    |
| `Other`            |
