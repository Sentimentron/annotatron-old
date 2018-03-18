-- Copyright 2018 Richard Townsend
-- Use is governed by the LICENSE file.

-- Using for various hasing algorithms
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Primary corpus information
CREATE TABLE IF NOT EXISTS an_corpora (
  id bigserial primary key,
  name text unique not null,
  description text
);

-- Used for checksumming asset byte contents.
CREATE OR REPLACE FUNCTION sha1(bytea) returns text AS $$
  SELECT encode(digest($1, 'sha512'), 'hex')
$$ LANGUAGE SQL STRICT IMMUTABLE;

DROP TABLE IF EXISTS an_assets;
CREATE TABLE IF NOT EXISTS an_assets (
  id bigserial primary key,
  name text unique not null,
  kind text not null,
  mime_type text not null,
  corpus_id bigserial references an_corpora(id) on delete cascade,
  binary_content bytea not null,
  date_uploaded timestamptz not null default 'now',
  sha_512_sum text not null,
  metadata jsonb,
  CHECK(sha1(binary_content) = sha_512_sum)
);
