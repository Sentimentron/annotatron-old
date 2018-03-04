-- Copyright 2018 Richard Townsend
-- Use is governed by the LICENSE file.

CREATE TABLE IF NOT EXISTS an_corpora (
  id bigserial primary key,
  name text unique not null,
  description text,
  question_generator text
);

DROP TABLE IF EXISTS an_assets;
CREATE TABLE IF NOT EXISTS an_assets (
  id bigserial primary key,
  name text unique not null,
  kind text not null,
  mime_type text not null,
  corpus_id bigserial references an_corpora(id) on delete cascade,
  binary_content bytea not null,
  date_uploaded timestamptz not null default 'now'
);
