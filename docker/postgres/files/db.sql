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
  id bigserial PRIMARY KEY,
  username text UNIQUE NOT NULL,
  created timestamptz NOT NULL DEFAULT 'now',
  email text NOT NULL,
  -- Salt is also stored in this field
  password bytea NOT NULL,
  password_last_changed timestamptz NULL,
  role an_user_type_v1 NOT NULL,
  random_seed text NOT NULL,
  deactivated_on timestamptz,
  password_reset_needed boolean NOT NULL default FALSE
);

CREATE TABLE IF NOT EXISTS an_user_tokens (
  id bigserial PRIMARY KEY,
  user_id bigint REFERENCES an_users(id),
  expires timestamptz NOT NULL,
  token text NOT NULL
);

-- Primary corpus information
CREATE TABLE IF NOT EXISTS an_corpora (
  id bigserial PRIMARY KEY,
  name text UNIQUE NOT NULL,
  description text,
  created timestamptz NOT NULL DEFAULT 'now',
  copyright_usage_restrictions text
);

CREATE INDEX IF NOT EXISTS an_corpora_name ON an_corpora(name);

-- Primary asset table.
CREATE TABLE IF NOT EXISTS an_assets (
  id bigserial PRIMARY KEY,
  name text NOT NULL,
  content bytea NOT NULL,
  user_metadata jsonb,
  date_uploaded timestamptz NOT NULL DEFAULT 'now',
  copyright_usage_restrictions text,
  checksum text NOT NULL,
  mime_type text NOT NULL,
  type_description text NOT NULL,
  corpus_id bigint NOT NULL REFERENCES an_corpora(id),
  uploader_id bigint NOT NULL REFERENCES an_users(id),
  CHECK(sha512(content) = checksum),
  UNIQUE(name, corpus_id)
);

CREATE TABLE IF NOT EXISTS an_annotations (
  id bigserial PRIMARY KEY,
  source an_annotation_source_v1 NOT NULL,
  summary_code text NOT NULL,
  created timestamptz NOT NULL DEFAULT 'now',
  kind text NOT NULL,
  content jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS an_questions (
  id         BIGSERIAL PRIMARY KEY,
  kind       TEXT        NOT NULL,
  content    JSONB       NOT NULL,
  summary_code TEXT NOT NULL,
  created    TIMESTAMPTZ NOT NULL DEFAULT 'now',
  creator_id BIGINT      NOT NULL REFERENCES an_users (id),
  corpus_id  BIGINT      NOT NULL REFERENCES an_corpora (id)
);


CREATE TABLE IF NOT EXISTS an_assignments_old (
  id bigserial PRIMARY KEY,
  summary_code text NOT NULL,
  question jsonb NOT NULL,
  response jsonb,
  assigned_annotator_id bigint NOT NULL REFERENCES an_users(id),
  assigned_user_id bigint NOT NULL REFERENCES an_users(id),
  assigned_reviewer_id bigint REFERENCES an_users(id),
  actual_reviewer_id bigint REFERENCES an_users(id),
  corpus_id bigint NOT NULL references an_corpora(id),
  completed timestamptz,
  reviewed timestamptz,
  annotator_notes text,
  reviewer_notes text,
  original_annotation_id bigint REFERENCES an_annotations(id),
  corrected_annotation_id bigint REFERENCES an_annotations(id)
);

CREATE TABLE IF NOT EXISTS an_assignments (
  id BIGSERIAL NOT NULL,
  summary_code text NOT NULL,
  assigned_user_id bigint REFERENCES an_users(id),
  annotator_id bigint NOT NULL REFERENCES an_users(id),
  reviewer_id bigint NOT NULL REFERENCES an_users(id),
  corpus_id bigint NOT NULL references an_corpora(id),
  created timestamptz NOT NULL DEFAULT 'now',
  updated timestamptz NOT NULL DEFAULT 'now',
  completed timestamptz,
  question jsonb NOT NULL,
  response jsonb,
  state text NOT NULL default 'created',
  CHECK(!(state == 'approved' && (response IS NULL))),
  CHECK(!(state != 'approved' && (assigned_user_id IS NULL)))
);

CREATE TABLE IF NOT EXISTS an_assignment_history(
  id BIGSERIAL PRIMARY KEY,
  assignment_id BIGINT NOT NULL REFERENCES an_assignment(id),
  updated_on timestamptz NOT NULL,
  state text NOT NULL,
  notes text,
  response jsonb,
  user_id bigint NOT NULL REFERENCES an_users(id)
);

CREATE TABLE IF NOT EXISTS an_assignments_assets_xref (
  id            BIGSERIAL PRIMARY KEY,
  assignment_id BIGINT REFERENCES an_assignments (id),
  asset_id      BIGINT REFERENCES an_assets (id)
);

--CREATE INDEX IF NOT EXISTS an_annotations_asset_summary_code_idx ON an_annotations (asset_id, summary_code, source);
