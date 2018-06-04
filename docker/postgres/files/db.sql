-- Copyright 2018 Richard Townsend
-- Use is governed by the LICENSE file.

-- Using for various hasing algorithms
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Used for checksum of asset bytes.
CREATE OR REPLACE FUNCTION sha512(bytea) returns text AS $$
  SELECT encode(digest($1, 'sha512'), 'hex')
$$ LANGUAGE SQL STRICT IMMUTABLE;

-- Create various types, if they do not exist
DO $$ BEGIN
  CREATE TYPE an_user_type_v1 AS ENUM ('Administrator', 'Staff', 'Reviewer', 'Annotator');
  EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
DO $$ BEGIN
  CREATE TYPE an_annotation_source_v1 AS ENUM ('Reference', 'SystemGenerated', 'Human', 'Aggregated');
  EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Primary user table
CREATE TABLE IF NOT EXISTS an_users (
  id                    BIGSERIAL PRIMARY KEY,
  username              TEXT UNIQUE     NOT NULL,
  created               TIMESTAMPTZ     NOT NULL DEFAULT 'now',
  email                 TEXT            NOT NULL,
  -- Salt is also stored in this field
  password              BYTEA           NOT NULL,
  password_last_changed TIMESTAMPTZ     NULL,
  role                  AN_USER_TYPE_V1 NOT NULL,
  random_seed           TEXT            NOT NULL,
  deactivated_on        TIMESTAMPTZ,
  password_reset_needed BOOLEAN         NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS an_user_tokens (
  id      BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES an_users (id),
  expires TIMESTAMPTZ NOT NULL,
  token   TEXT        NOT NULL
);

-- Primary corpus information
CREATE TABLE IF NOT EXISTS an_corpora (
  id                           BIGSERIAL PRIMARY KEY,
  name                         TEXT UNIQUE NOT NULL,
  description                  TEXT,
  created                      TIMESTAMPTZ NOT NULL DEFAULT 'now',
  copyright_usage_restrictions TEXT
);

CREATE INDEX IF NOT EXISTS an_corpora_name ON an_corpora(name);

-- Primary asset table.
CREATE TABLE IF NOT EXISTS an_assets (
  id                           BIGSERIAL PRIMARY KEY,
  name                         TEXT        NOT NULL,
  content                      BYTEA       NOT NULL,
  user_metadata                JSONB,
  date_uploaded                TIMESTAMPTZ NOT NULL DEFAULT 'now',
  copyright_usage_restrictions TEXT,
  checksum                     TEXT        NOT NULL,
  mime_type                    TEXT        NOT NULL,
  type_description             TEXT        NOT NULL,
  corpus_id                    BIGINT      NOT NULL REFERENCES an_corpora (id),
  uploader_id                  BIGINT      NOT NULL REFERENCES an_users (id),
  CHECK (sha512(content) = checksum),
  UNIQUE (name, corpus_id)
);

CREATE TABLE IF NOT EXISTS an_annotations (
  id           BIGSERIAL PRIMARY KEY,
  source       AN_ANNOTATION_SOURCE_V1 NOT NULL,
  summary_code TEXT                    NOT NULL,
  created      TIMESTAMPTZ             NOT NULL DEFAULT 'now',
  kind         TEXT                    NOT NULL,
  content      JSONB                   NOT NULL
);

CREATE TABLE IF NOT EXISTS an_questions (
  id           BIGSERIAL PRIMARY KEY,
  kind         TEXT        NOT NULL,
  content      JSONB       NOT NULL,
  summary_code TEXT        NOT NULL,
  created      TIMESTAMPTZ NOT NULL DEFAULT 'now',
  creator_id   BIGINT      NOT NULL REFERENCES an_users (id),
  corpus_id    BIGINT      NOT NULL REFERENCES an_corpora (id)
);


CREATE TABLE IF NOT EXISTS an_assignments_old (
  id                      BIGSERIAL PRIMARY KEY,
  summary_code            TEXT   NOT NULL,
  question                JSONB  NOT NULL,
  response                JSONB,
  assigned_annotator_id   BIGINT NOT NULL REFERENCES an_users (id),
  assigned_user_id        BIGINT NOT NULL REFERENCES an_users (id),
  assigned_reviewer_id    BIGINT REFERENCES an_users (id),
  actual_reviewer_id      BIGINT REFERENCES an_users (id),
  corpus_id               BIGINT NOT NULL REFERENCES an_corpora (id),
  completed               TIMESTAMPTZ,
  reviewed                TIMESTAMPTZ,
  annotator_notes         TEXT,
  reviewer_notes          TEXT,
  original_annotation_id  BIGINT REFERENCES an_annotations (id),
  corrected_annotation_id BIGINT REFERENCES an_annotations (id)
);

CREATE TABLE IF NOT EXISTS an_assignments (
  id               BIGSERIAL   NOT NULL PRIMARY KEY,
  summary_code     TEXT        NOT NULL,
  assigned_user_id BIGINT REFERENCES an_users (id),
  annotator_id     BIGINT      NOT NULL REFERENCES an_users (id),
  reviewer_id      BIGINT REFERENCES an_users (id),
  corpus_id        BIGINT      NOT NULL REFERENCES an_corpora (id),
  created          TIMESTAMPTZ NOT NULL DEFAULT 'now',
  updated          TIMESTAMPTZ NOT NULL DEFAULT 'now',
  completed        TIMESTAMPTZ,
  question         JSONB       NOT NULL,
  response         JSONB,
  state            TEXT        NOT NULL DEFAULT 'created',
  CHECK (NOT ((state = 'approved') AND (response IS NULL))),
  CHECK (NOT ((state != 'approved') AND (assigned_user_id IS NULL)))
);

CREATE TABLE IF NOT EXISTS an_assignment_history (
  id               BIGSERIAL PRIMARY KEY,
  assignment_id    BIGINT      NOT NULL REFERENCES an_assignments (id),
  updating_user_id BIGINT      NOT NULL REFERENCES an_users (id),
  updated_on       TIMESTAMPTZ NOT NULL,
  state            TEXT        NOT NULL,
  notes            TEXT,
  response         JSONB
);

CREATE TABLE IF NOT EXISTS an_assignments_assets_xref (
  id            BIGSERIAL PRIMARY KEY,
  assignment_id BIGINT REFERENCES an_assignments (id),
  asset_id      BIGINT REFERENCES an_assets (id)
);

--CREATE INDEX IF NOT EXISTS an_annotations_asset_summary_code_idx ON an_annotations (asset_id, summary_code, source);
