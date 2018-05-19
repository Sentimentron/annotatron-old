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
  id      BIGSERIAL PRIMARY KEY,
  content JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS an_questions (
  id                               BIGSERIAL PRIMARY KEY,
  human_prompt                     TEXT        NOT NULL,
  kind                             TEXT        NOT NULL,
  summary_code                     TEXT        NOT NULL,
  created                          TIMESTAMPTZ NOT NULL DEFAULT 'now',
  annotation_instructions          TEXT,
  detailed_annotation_instructions TEXT,
  -- This field is left under-specified, see the OpenAPI spec for what this field contains.
  question_content                 JSONB
);

CREATE TABLE IF NOT EXISTS an_multiple_choice_questions (
  question_id BIGINT PRIMARY KEY REFERENCES an_questions(id),
  choices jsonb NOT NULL,
  CHECK(json_array_length(choices) > 0)
);

CREATE TABLE IF NOT EXISTS an_1d_range_questions (
  question_id BIGINT PRIMARY KEY REFERENCES an_questions (id),
  minimum_segments INT NULL,
  maximum_segments INT NULL,
  choices jsonb NOT NULL,
  freeform_allowed boolean NOT NULL,
  can_overlap boolean NOT NULL,
  CHECK(minimum_segments < maximum_segments),
  -- Not allowing free-form input implies that choice is not NULL
  CHECK(json_array_length(choices) > 0 || freeform_allowed)
);

CREATE TABLE IF NOT EXISTS an_1d_segmentation_questions (
  question_id BIGINT PRIMARY KEY REFERENCES an_questions (id),
  minimum_segments INT NULL,
  maximum_segments INT NULL,
  choices jsonb NOT NULL,
  freeform_allowed boolean NOT NULL,
  can_overlap boolean NOT NULL,
  CHECK(minimum_segments < maximum_segments),
  -- Not allowing free-form input implies that choice is not NULL
  CHECK(json_array_length(choices) > 0 || freeform_allowed)
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
