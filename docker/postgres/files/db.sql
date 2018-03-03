-- Copyright 2018 Richard Townsend
-- Use is governed by the LICENSE file.

CREATE TABLE IF NOT EXISTS auth_user (
  id bigserial primary key
);

ALTER TABLE auth_user OWNER to annotatron;

ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS password text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS last_login timestamptz;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS is_superuser boolean NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS username text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS first_name text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS last_name text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS email text NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS is_staff boolean NOT NULL;
ALTER TABLE auth_user ADD COLUMN IF NOT EXISTS date_joined timestamptz NOT NULL;

CREATE TABLE IF NOT EXISTS django_session (
  id bigserial primary key
);

ALTER TABLE django_session ADD COLUMN IF NOT EXISTS session_key text NOT NULL;
ALTER TABLE django_session ADD COLUMN IF NOT EXISTS session_data text NOT NULL;
ALTER TABLE django_session ADD COLUMN IF NOT EXISTS expire_date timestamptz NOT NULL;

CREATE TABLE IF NOT EXISTS django_content_type (
  id bigserial primary key,
  name text,
  app_label text,
  model text
);

CREATE TABLE IF NOT EXISTS django_admin_log (
  id bigserial primary key,
  action_time timestamptz DEFAULT 'now' NOT NULL,
  object_id text,
  object_repr text,
  action_flag int,
  change_message text,
  content_type_id bigserial references django_content_type(id),
  user_id bigserial references auth_user(id)
);

CREATE TABLE IF NOT EXISTS an_blobs (
  id bigserial primary key,
  blob bytea NOT NULL,
  date_inserted timestamptz DEFAULT 'now' NOT NULL
);
