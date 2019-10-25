-- Copyright 2019 Tigerwing(tigerwingxys@qq.com)
--
-- Licensed under the Apache License, Version 2.0 (the "License"); you may
-- not use this file except in compliance with the License. You may obtain
-- a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
-- WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
-- License for the specific language governing permissions and limitations
-- under the License.
--
-- this file created at 2019.8.27

-- To create the database:
--   CREATE DATABASE blog;
--   CREATE USER blog WITH PASSWORD 'blog';
--   GRANT ALL ON DATABASE blog TO blog;
--
-- To reload the tables:
--   psql -U blog -d blog < schema.sql

DROP TABLE IF EXISTS authors;
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(100) NOT NULL
);

DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    id SERIAL PRIMARY KEY,
    author_id INT NOT NULL REFERENCES authors(id),
    slug VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(512) NOT NULL,
    markdown TEXT NOT NULL,
    html TEXT NOT NULL,
    published TIMESTAMP NOT NULL,
    updated TIMESTAMP NOT NULL,
    is_public boolean not null default true
);
create index entries_author_id_idx on entries(author_id);
create index entries_slug_idx on entries(slug);


drop table if exists cache_flag;
create table cache_flag(
    cache_name varchar(32) primary key,
    time_flag timestamp not null,
    int_flag int not null
);
insert into cache_flag values('entry',current_timestamp ,0);
create function update_entry_cach_flag()
returns trigger as $$
begin
    update cache_flag set time_flag = new.published where cache_name = 'entry';
    return NEW;
end; $$
language "plpgsql";
create trigger entry_cache_flag_trigger after insert on entries for each row execute procedure update_entry_cach_flag ();


