-- Copyright 2018 Richard Townsend
-- Use is governed by the LICENSE file.

CREATE TABLE IF NOT EXISTS auth_user (
  id bigserial primary key
);

ALTER TABLE auth_user OWNER to annotatron;

ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS password bytea;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS last_login timestamptz;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS is_superuser boolean NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS username text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS first_name text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS last_name text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS email text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS is_staff boolean NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS date_joined timestamptz NOT NULL;
