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
  deactivated_on timestamptz
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
  content bytea NOT NULL,
  metadata jsonb,
  date_uploaded timestamptz NOT NULL DEFAULT 'now',
  copyright_usage_restrictions text,
  checksum text NOT NULL,
  mime_type text NOT NULL,
  type_description text NOT NULL,
  CHECK(sha512(content) = checksum)
);

CREATE TABLE IF NOT EXISTS an_asset_corpus_xref (
  id bigserial PRIMARY KEY,
  asset_id bigint NOT NULL REFERENCES an_assets(id),
  corpus_id bigint NOT NULL REFERENCES an_corpora(id),
  unique_name text NOT NULL,
  unique(corpus_id, unique_name)
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
  id bigserial PRIMARY KEY,
  human_prompt text NOT NULL,
  kind text NOT NULL,
  summary_code text NOT NULL,
  created timestamptz NOT NULL DEFAULT 'now',
  annotation_instructions text,
  detailed_annotation_instructions text
);

CREATE TABLE IF NOT EXISTS an_assignments (
  id bigserial PRIMARY KEY,
  question_id bigint NOT NULL REFERENCES an_questions(id),
  user_id bigint NOT NULL REFERENCES an_users(id),
  assigned_reviewer_id bigint REFERENCES an_users(id),
  actual_reviewer_id bigint REFERENCES an_users(id),
  created timestamptz NOT NULL DEFAULT 'now',
  completed timestamptz,
  reviewed timestamptz,
  annotator_notes text,
  reviewer_notes text,
  original_annotation_id bigint REFERENCES an_annotations(id),
  corrected_annotation_id bigint REFERENCES an_annotations(id)
);


--CREATE INDEX IF NOT EXISTS an_annotations_asset_summary_code_idx ON an_annotations (asset_id, summary_code, source);
