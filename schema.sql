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

CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(100) NOT NULL
);

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

insert into cache_flag(cache_name, time_flag, int_flag, author_id) values('catalog',current_timestamp ,0,0);

#add 2019-10-31

# 2019-11-5
alter table authors add column activate_key varchar (32) not null default 'KEY';
alter table authors add column activate_state boolean default false ;
alter table authors add column create_date timestamp default current_timestamp ;
update authors set activate_state=true where activate_key='KEY';

# 2019-11-11
drop trigger author_del_catalog_trigger on authors;
drop function author_del_catalog;
drop trigger catalogs_update_cat_trigger on catalogs;
drop trigger catalogs_delete_cat_trigger on catalogs;
drop trigger entry_cache_flag_trigger on entries;
drop function update_entry_cache_flag;
drop trigger catalogs_add_cat_trigger on catalogs;
drop function catalogs_add_stat;
drop trigger author_add_catalog_trigger on authors;
drop function author_add_catalog;

alter table cache_flag add column author_id int not null default 0;
alter table cache_flag drop constraint cache_flag_pkey;
alter table cache_flag add constraint cache_flag_pkey primary key (author_id,cache_name);
insert into cache_flag(cache_name,time_flag,int_flag,author_id)  select 'catalog',current_timestamp,0,id from authors where id!=0;

# 2019-11-13 not flush to vultr
alter table authors add column settings text not null default '{"default-editor": "kind-editor"}';
alter table entries add column editor varchar (32) not null default 'kind-editor';

# 2019-11-17
alter table authors add column quota int not null default 50;
alter table entries add column size int not null default 280;
alter table entries add column attach_size int not null default 0;
create table author_operation (
    author_id int not null,
    operate varchar (32) not null,
    remote_ip varchar (18) not null,
    operate_date timestamp not null default current_timestamp ,
    info text
);
create index author_operation_idx on author_operation(author_id,operate_date);

alter table entries add column state int not null default 1;