-- Some conventions
--
-- * SQL KEYWORDS IN CAPS
-- * identifiers in lower case
-- * all field names are prefixed by table name and an underscore
-- * specify NOT NULL.  Do not specify NULL, it's the default, non-standard, and discouraged.
-- * use TIMESTAMP WITHOUT TIME ZONE for all date/times
--   (The default "WITH TIME ZONE" is more appropriate for calendar apps)
-- * use UUIDs as the surrogate key.  They're only 128 bits dispite appearances.

CREATE TABLE account (
	account_id							UUID DEFAULT gen_random_uuid() PRIMARY KEY,
	account_username					VARCHAR(255) NOT NULL,
	account_fullname					VARCHAR(255) NOT NULL,
	account_phone                       VARCHAR(20) NOT NULL,
	account_password_hash				VARCHAR(255) NOT NULL,
	account_forgot_token_hash			VARCHAR(255),
	account_forgot_requested			TIMESTAMP WITHOUT TIME ZONE,
	account_created						TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
	account_is_admin					BOOLEAN NOT NULL DEFAULT false,
	account_is_employee					BOOLEAN NOT NULL DEFAULT false,
	account_has_training				BOOLEAN NOT NULL DEFAULT false,
	account_status				        VARCHAR(64) NOT NULL CHECK (account_status IN ('active', 'disabled'))
);

CREATE TABLE email (
	email_id					UUID DEFAULT gen_random_uuid() PRIMARY KEY,
	email_account_id			UUID NOT NULL REFERENCES account (account_id) ON DELETE RESTRICT,
	email_address				VARCHAR(255) NOT NULL UNIQUE,
	email_created				TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
	email_verified				TIMESTAMP WITHOUT TIME ZONE
);
