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
alter table entries add column is_encrypt boolean not null default false;
alter table entries add column search_tags varchar (256);
alter table entries add column cat_id int not null references catalogs(cat_id) default 12;



drop table if exists cache_flag;
create table cache_flag(
    cache_name varchar(32) primary key,
    time_flag timestamp not null,
    int_flag int not null
);

create table catalogs (
    cat_id int primary key,
    cat_name varchar(64) not null ,
    author_id int not null references authors(id),
    parent_id int not null,
    create_date timestamp default current_timestamp
);
create index catalogs_parent_idx on catalogs(author_id,parent_id) ;
#系统内置分类
insert into authors (id,email,name,hashed_password) values(0,'system@inmountains.com','system','system');
insert into catalogs (author_id,cat_id,parent_id,cat_name ) values(0, 11, 0, '日记');
insert into catalogs (author_id,cat_id,parent_id,cat_name ) values(0, 12, 0, '博客');
insert into catalogs (author_id,cat_id,parent_id,cat_name ) values(0, 13, 0, '工作');

#add 20191030
drop table entries_statistic;
create table entries_statistic(
    author_id int not null references authors(id),
    cat_id int not null references catalogs(cat_id),
    parent_id int not null,
    entries_cnt int default 0
);
alter table entries_statistic add constraint entries_statistic_pk primary key (author_id,cat_id);
drop trigger catalogs_add_cat_trigger on catalogs;
drop function catalogs_add_stat;
create function catalogs_add_stat()
returns trigger as $$
begin
    insert into entries_statistic (author_id,cat_id,parent_id) values (new.author_id, new.cat_id, new.parent_id);
    update cache_flag set time_flag = new.create_date where cache_name = 'catalog';
    return new;
end;$$
language "plpgsql";
create trigger catalogs_add_cat_trigger after insert on catalogs for each row execute procedure catalogs_add_stat();

drop trigger author_add_catalog_trigger on authors;
drop function author_add_catalog;
create function author_add_catalog()
returns trigger as $$
begin
    insert into entries_statistic(author_id,cat_id,parent_id) select new.id,cat_id,parent_id from catalogs where author_id=0;
    return new;
end;$$
language "plpgsql";
create trigger author_add_catalog_trigger after insert on authors for each row execute procedure author_add_catalog();

insert into cache_flag values('catalog',current_timestamp ,0);
drop trigger entry_cache_flag_trigger on entries;
drop function update_entry_cache_flag;
create function update_entry_cache_flag()
returns trigger as $$
begin
    update cache_flag set time_flag = new.published where cache_name = 'entry' or cache_name = 'catalog';
    update entries_statistic set entries_cnt = entries_cnt +1 where author_id=new.author_id and cat_id=new.cat_id;
    return NEW;
end; $$
language "plpgsql";
create trigger entry_cache_flag_trigger after insert on entries for each row execute procedure update_entry_cache_flag ();
