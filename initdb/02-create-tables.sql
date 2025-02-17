-- Some conventions
--
-- * SQL KEYWORDS IN CAPS
-- * identifiers in lower case
-- * all field names are prefixed by table name and an underscore
-- * specify NOT NULL.  Do not specify NULL, it's the default, non-standard, and discouraged.
-- * use TIMESTAMP WITHOUT TIME ZONE for all date/times
--   (The default "WITH TIME ZONE" is more appropriate for calendar apps)
-- * use UUIDs as the surrogate key.  They're only 128 bits dispite appearances.


DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'account') THEN
    CREATE TABLE account (
        account_id							UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        account_username					VARCHAR(255) NOT NULL UNIQUE,
        account_fullname					VARCHAR(255) NOT NULL,
        account_phone                       VARCHAR(20) NOT NULL UNIQUE,
        account_password_hash				VARCHAR(255) NOT NULL,
        account_forgot_token_hash			VARCHAR(255),
        account_forgot_requested			TIMESTAMP WITHOUT TIME ZONE,
        account_last_login                  TIMESTAMP,
        account_is_admin					BOOLEAN NOT NULL DEFAULT false,
        account_commission_rate             DECIMAL(5, 2) CHECK (account_commission_rate >= 0 AND account_commission_rate <= 100),
        account_status				        VARCHAR(64) NOT NULL CHECK (account_status IN ('active', 'disabled')),
        account_created						TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        account_updated_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  END IF;

  IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'email') THEN
    CREATE TABLE email (
        email_id					UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        email_account_id			UUID NOT NULL REFERENCES account (account_id) ON DELETE RESTRICT,
        email_address				VARCHAR(255) NOT NULL UNIQUE,
        email_created				TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        email_verified				TIMESTAMP WITHOUT TIME ZONE,
        email_verification_token    UUID
    );
  END IF;

  IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'telegram') THEN
    CREATE TABLE telegram (
        telegram_id                         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        telegram_account_id                 UUID NOT NULL REFERENCES account(account_id) ON DELETE CASCADE,
        telegram_username                   VARCHAR(255) UNIQUE,
        telegram_verified                   BOOLEAN NOT NULL DEFAULT false,
        telegram_verification_token         UUID,
        telegram_is_admin                   BOOLEAN NOT NULL DEFAULT false,
        telegram_created                    TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
  END IF;


  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_method_enum') THEN
    CREATE TYPE payment_method_enum AS ENUM (
      'Cash', 'Check', 'Card', 'Venmo', 'PayPal', 'CashApp', 'Bank Transfer', 'Other'
    );
  END IF;

  IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'job_report') THEN
    CREATE TABLE job_report (
        job_report_id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        report_by_account_id        UUID REFERENCES account(account_id) ON DELETE RESTRICT,
        latitude                    DECIMAL(10, 8),
        longitude                   DECIMAL(11, 8),
        created_at                 TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        amount_received_dollars     DECIMAL(10, 2) NOT NULL,
        payment_method              payment_method_enum,
        job_description             TEXT,
        client_name                 VARCHAR(255),
        client_contact              VARCHAR(255),
        job_status                  VARCHAR(50) DEFAULT 'completed' CHECK (job_status IN ('pending', 'in_progress', 'completed', 'cancelled')),
        notes                       TEXT,
        updated_at                  TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
  END IF;

  IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'report_photos') THEN
    CREATE TABLE report_photos (
        photo_id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        photo_job_report_id         UUID REFERENCES job_report(job_report_id) ON DELETE CASCADE,
        photo_url                   VARCHAR(255) NOT NULL,
        file_name                   VARCHAR(255) NOT NULL,
        file_size                   INTEGER NOT NULL,
        created_at                  TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
  END IF;

END
$$;
