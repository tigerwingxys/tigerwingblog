#!/usr/bin/env python3
#
# Copyright 2019 Tigerwing(tigerwingxys@qq.com)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# this file created at 2019.8.27

from infrastructure.data.bases import BaseTable
from infrastructure.utils.db_conn import DbConnect
from data.cache_flag import CacheFlag
from data.entries_statistic import EntriesStatistic


import unicodedata
import re
from cachetools import cached, TTLCache
import datetime
from infrastructure.utils.common import get_size
import os

max_fetch_size = 1000
one_entry_init_size = 280

cached_entries = dict()


class Entry(BaseTable):
    def __init__(self):
        self.cached = False

    async def get_empty_entry(self, author_id, cat_id=None, editor=None):
        entry = DbConnect.query_one("select nextval('entries_id_seq') as id")
        entry.cat_id = cat_id
        entry.editor = editor
        entry.title = datetime.datetime.now().strftime('%Y-%m-%d(%A)') if cat_id == '11' else ""
        entry.is_public = False
        entry.is_encrypt = False
        entry.search_tags = datetime.datetime.now().strftime('%Y-%m') if cat_id == '11' else ""
        entry.author_id = author_id
        entry.markdown = ""
        entry.html = ""
        entry.slug = ""
        entry.size = one_entry_init_size
        entry.attach_size = 0
        return entry

    async def add_entry(self, author, entry_id, title, text, html, is_public, is_encrypt, search_tags, cat_id):
        slug = unicodedata.normalize("NFKD", author.name+'-'+str(datetime.datetime.now()))
        slug = re.sub(r"[^\w]+", " ", slug)
        slug = "-".join(slug.lower().strip().split())
        slug = slug.encode("ascii", "ignore").decode("ascii")
        if not slug:
            slug = "entry"
        while True:
            e = DbConnect.query_check("SELECT * FROM entries WHERE slug = %s", slug)
            if not e:
                break
            slug += "-2"
        ss = eval(author.settings)
        size = one_entry_init_size + len(text) + len(html)
        fpath = os.path.join(author.app_settings['upload_path'], str(author.id), entry_id)
        attach_cnt, attach_size = get_size(fpath)
        entry = DbConnect.execute_returning(
            "INSERT INTO entries (id,author_id,title,slug,markdown,html,is_public,is_encrypt,search_tags,cat_id,editor,size,attach_size,attach_cnt,published,updated)"
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP) returning published as create_date",
            entry_id, author.id, title, slug, text, html, is_public, is_encrypt, search_tags, cat_id, ss["default-editor"],size,attach_size,attach_cnt)
        EntriesStatistic().plus_one(author.id, cat_id)
        CacheFlag().update_cache_flag("entry", new_time=entry.create_date)
        CacheFlag().update_cache_flag("catalog", new_time=entry.create_date, author_id=author.id)
        return slug

    async def update(self, author, entry_id, title, text, html, is_public, is_encrypt, search_tags, cat_id):
        entry = DbConnect.execute_returning(
            "UPDATE entries SET title = %s, markdown = %s, html = %s , is_public = %s , updated=current_timestamp, "
            "is_encrypt=%s, search_tags=%s, cat_id=%s, size = %s "
            "WHERE id = %s returning slug,updated as create_date",
            title, text, html, is_public, is_encrypt, search_tags, cat_id, one_entry_init_size+len(text)+len(html), int(entry_id))
        CacheFlag().update_cache_flag("entry", new_time=entry.create_date)
        CacheFlag().update_cache_flag("catalog", new_time=entry.create_date, author_id=author.id)
        return entry

    async def delete(self, author_id, entry_id, cat_id):
        DbConnect.execute("update entries set state=0 where id=%s", entry_id)
        EntriesStatistic().minus_one(author_id, cat_id)
        CacheFlag().update_cache_flag("entry")
        CacheFlag().update_cache_flag("catalog", author_id=author_id)

    async def add_attach(self, entry_id, size):
        DbConnect.execute("update entries set attach_size=(attach_size+%s), attach_cnt=attach_cnt+1 where id=%s", size, entry_id)
        CacheFlag().update_cache_flag("entry")

    async def delete_attach(self, entry_id, size):
        DbConnect.execute("update entries set attach_size=(attach_size-%s), attach_cnt=attach_cnt-1 where id=%s", size, entry_id)
        CacheFlag().update_cache_flag("entry")

    async def get(self, entry_id=None, slug=None):
        if entry_id is not None:
            return DbConnect.query_one("SELECT * FROM entries WHERE id = %s and state=1", int(entry_id))
        if slug is not None:
            return DbConnect.query_one("SELECT * FROM entries WHERE slug = %s", slug)
        return None

    async def is_exists(self, entry_id=None, slug=None):
        if entry_id is not None:
            return DbConnect.query_check("SELECT * FROM entries WHERE id = %s", int(entry_id))
        if slug is not None:
            return DbConnect.query_check("SELECT * FROM entries WHERE slug = %s", slug)
        return False

    async def get_shared(self, position_offset=0, fetch_size=None):
        global cached_entries
        author_id = 0
        if author_id not in cached_entries.keys():
            cached_entries[author_id] = dict()
            cached_entries[author_id]["cache_query_time"] = datetime.datetime(2000,1,1)
            cached_entries[author_id]["entries"] = []

        cache_time = CacheFlag().get_cache_flag(cache_name="entry")["time_flag"]
        if cached_entries[author_id]["cache_query_time"] < cache_time:
            global max_fetch_size
            if fetch_size is not None and fetch_size > max_fetch_size:
                fetch_size = max_fetch_size
            cached_entries[author_id]["entries"] = \
                DbConnect.query("SELECT entries.*,authors.name as author_name FROM entries "
                                "inner join authors on authors.id=entries.author_id "
                                "where entries.is_public = true and entries.state=1 order by entries.published desc ",
                                position_offset, fetch_size)
            cached_entries[author_id]["key_entries"] = self.analyze_tags(cached_entries[author_id]["entries"])
            cached_entries[author_id]["cache_query_time"] = cache_time

        return cached_entries[author_id]["entries"], cached_entries[author_id]["key_entries"]

    async def get_entries_by_author(self, author_id, cat_id='0', position_offset=0, fetch_size=None):
        if author_id is None or author_id == 0:
            return await self.get_shared(position_offset, fetch_size)
        global cached_entries
        if cat_id is None or len(cat_id) == 0:
            cat_id = '0'
        key = "%d%s" % (author_id, cat_id)
        if author_id not in cached_entries.keys():
            cached_entries[key] = dict()
            cached_entries[key]["cache_query_time"] = datetime.datetime(2000, 1, 1)
            cached_entries[key]["entries"] = []

        cache_time = CacheFlag().get_cache_flag(cache_name="entry")["time_flag"]
        if cached_entries[key]["cache_query_time"] < cache_time:
            global max_fetch_size
            if fetch_size is not None and fetch_size > max_fetch_size:
                fetch_size = max_fetch_size
            if cat_id == '0':
                cached_entries[key]["entries"] = \
                    DbConnect.query("SELECT entries.*,authors.name as author_name FROM entries "
                                    "inner join authors on authors.id=entries.author_id "
                                    "where entries.author_id=%s and entries.state=1 order by entries.published desc ",
                                    position_offset, fetch_size, author_id)
            else:
                cached_entries[key]["entries"] = \
                    DbConnect.query("SELECT entries.*,authors.name as author_name FROM entries "
                                    "inner join authors on authors.id=entries.author_id "
                                    "where entries.author_id=%s and entries.cat_id=%s "
                                    "and entries.state=1 order by entries.published desc ",
                                    position_offset, fetch_size, author_id, cat_id)
            cached_entries[key]["key_entries"] = self.analyze_tags(cached_entries[key]["entries"])
            cached_entries[key]["cache_query_time"] = cache_time

        return cached_entries[key]["entries"], cached_entries[key]["key_entries"]

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    async def search(self, search_text, author_id = None):
        result = []
        if author_id is not None:
            entries, key_entries = await self.get_entries_by_author(author_id)
            for entry in entries:
                if re.search(search_text, entry["title"]) or (entry["search_tags"] and re.search(search_text, entry["search_tags"])) \
                        or re.search(search_text, entry["html"]):
                    result.append(entry)

        entries, key_entries = await self.get_shared()
        if author_id is not None:
            for entry in entries:
                if author_id == entry['author_id']:
                    continue
                if re.search(search_text, entry["title"]) or (entry["search_tags"] and re.search(search_text, entry["search_tags"])) \
                        or re.search(search_text, entry["html"]):
                    result.append(entry)
        else:
            for entry in entries:
                if re.search(search_text, entry["title"]) or (entry["search_tags"] and re.search(search_text, entry["search_tags"]))\
                        or re.search(search_text, entry["html"]):
                    result.append(entry)
        return result

    def analyze_tags(self, entries):
        key_entries = dict()
        for entry in entries:
            tags = entry["search_tags"]
            if tags is None:
                continue
            for key in tags.split():
                if key not in key_entries.keys():
                    key_entries[key] = []
                key_entries[key].append(entry)

        return key_entries

    async def get_usage_by_author(self, author_id):
        return DbConnect.query_one("select sum(size) as txt_usage, sum(attach_size) as attach_usage from entries where author_id=%s and state=1", author_id)
