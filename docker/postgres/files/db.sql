-- Copyright 2018 Richard Townsend
-- Use is governed by the LICENSE file.

CREATE TABLE IF NOT EXISTS an_corpora (
  id bigserial primary key,
  name text unique not null,
  description text,
  question_generator text
);
