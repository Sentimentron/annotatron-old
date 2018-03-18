-- Copyright 2018 Richard Townsend
-- Use is governed by the LICENSE file.

-- Using for various hasing algorithms
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Primary corpus information
CREATE TABLE IF NOT EXISTS an_corpora (
  id bigserial PRIMARY KEY,
  name text UNIQUE NOT NULL,
  description text
);

CREATE INDEX IF NOT EXISTS an_corpora_name ON an_corpora(name);

-- Used for checksum of asset bytes.
CREATE OR REPLACE FUNCTION sha1(bytea) returns text AS $$
  SELECT encode(digest($1, 'sha512'), 'hex')
$$ LANGUAGE SQL STRICT IMMUTABLE;

-- Primary asset table.
DROP TABLE IF EXISTS an_assets;
CREATE TABLE IF NOT EXISTS an_assets (
  id bigserial PRIMARY KEY,
  name text UNIQUE NOT NULL,
  kind text NOT NULL,
  mime_type text NOT NULL,
  corpus_id bigint NOT NULL REFERENCES an_corpora(id) ON DELETE CASCADE,
  binary_content bytea NOT NULL,
  date_uploaded timestamptz NOT NULL DEFAULT 'now',
  sha_512_sum text NOT NULL,
  metadata jsonb,
  CHECK(sha1(binary_content) = sha_512_sum),
  UNIQUE (name, corpus_id)
);

CREATE INDEX IF NOT EXISTS an_assets_corpus_idx ON an_assets(corpus_id);
CREATE INDEX IF NOT EXISTS an_assets_corpus_name_idx ON an_assets(corpus_id, name);
CREATE INDEX IF NOT EXISTS an_assets_corpus_checksum_idx ON an_assets(corpus_id, sha_512_sum);

-- Keeps the notion of annotators separate from a Django user.
DROP TABLE IF EXISTS an_annotators;
CREATE TABLE IF NOT EXISTS an_annotators (
  id bigserial PRIMARY KEY,
  external_id bigint NOT NULL,                  -- Undeclared link to the Django users table.
                                                -- Done like this so we can create the DB before migrations take place.
  created timestamptz NOT NULL DEFAULT 'now'
);

CREATE INDEX IF NOT EXISTS an_annotators_external_info ON an_annotators(external_id);

-- Primary annotations table, used for reference and user-contributed annotations.
DROP TABLE IF EXISTS an_annotations;
CREATE TABLE IF NOT EXISTS an_annotations (
  id bigserial PRIMARY KEY,
  asset_id bigserial NOT NULL REFERENCES an_assets(id) ON DELETE CASCADE,
  kind text NOT NULL,
  summary_code text NOT NULL,
  annotation jsonb NOT NULL,
  source integer NOT NULL,
  created timestamptz NOT NULL DEFAULT 'now',
  annotator bigserial REFERENCES an_annotators(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS an_annotations_asset_summary_code_idx ON an_annotations (asset_id, summary_code, source);
