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


import unicodedata
import re
from cachetools import cached, TTLCache
import datetime

max_fetch_size = 1000

cached_entries = dict()


class Entry(BaseTable):
    def __init__(self):
        self.cached = False

    async def add_entry(self, author, title, text, html, is_public, is_encrypt, search_tags, cat_id):
        slug = unicodedata.normalize("NFKD", author.name+'-'+str(datetime.datetime.now())+title)
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
        DbConnect.execute(
            "INSERT INTO entries (author_id,title,slug,markdown,html,is_public,is_encrypt,search_tags,cat_id,published,updated)"
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
            author.id, title, slug, text, html, is_public, is_encrypt, search_tags, cat_id)
        return slug

    async def update_entry(self, entry_id, title, text, html, is_public, is_encrypt, search_tags, cat_id):
        return DbConnect.execute_returning(
            "UPDATE entries SET title = %s, markdown = %s, html = %s , is_public = %s , updated=current_timestamp, "
            "is_encrypt=%s, search_tags=%s, cat_id=%s"
            "WHERE id = %s returning slug",
            title, text, html, is_public, is_encrypt, search_tags, cat_id, int(entry_id))

    async def get_entry(self, entry_id=None, slug=None):
        if entry_id is not None:
            return DbConnect.query_one("SELECT * FROM entries WHERE id = %s", int(entry_id))
        if slug is not None:
            return DbConnect.query_one("SELECT * FROM entries WHERE slug = %s", slug)
        return None

    async def is_exists(self, entry_id=None, slug=None):
        if entry_id is not None:
            return DbConnect.query_check(entry_id=int(entry_id))
        if slug is not None:
            return DbConnect.query_check(slug=slug)
        return False

    async def get_entries(self, position_offset=0, fetch_size=None):
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
            cached_entries[author_id]["entries"] = DbConnect.query("SELECT * FROM entries where is_public = true ORDER BY published DESC", position_offset, fetch_size)
            cached_entries[author_id]["key_entries"] = self.search_tags_entries(cached_entries[author_id]["entries"])
            cached_entries[author_id]["cache_query_time"] = cache_time

        return cached_entries[author_id]["entries"], cached_entries[author_id]["key_entries"]

    async def get_entries_by_author(self, author_id, cat_id=None, position_offset=0, fetch_size=None):
        if author_id is None or author_id == 0:
            return await self.get_entries(position_offset, fetch_size)
        global cached_entries
        key = "%d%s" % (author_id,cat_id)
        if author_id not in cached_entries.keys():
            cached_entries[key] = dict()
            cached_entries[key]["cache_query_time"] = datetime.datetime(2000, 1, 1)
            cached_entries[key]["entries"] = []

        cache_time = CacheFlag().get_cache_flag(cache_name="entry")["time_flag"]
        if cached_entries[key]["cache_query_time"] < cache_time:
            global max_fetch_size
            if fetch_size is not None and fetch_size > max_fetch_size:
                fetch_size = max_fetch_size
            if cat_id is None or len(cat_id) == 0:
                cached_entries[key]["entries"] = DbConnect.query("SELECT * FROM entries WHERE author_id = %s ORDER BY published DESC", position_offset, fetch_size, author_id)
            else:
                cached_entries[key]["entries"] = DbConnect.query("SELECT * FROM entries WHERE author_id = %s and cat_id = %s ORDER BY published DESC", position_offset, fetch_size, author_id, cat_id)
            cached_entries[key]["key_entries"] = self.search_tags_entries(cached_entries[key]["entries"])
            cached_entries[key]["cache_query_time"] = cache_time

        return cached_entries[key]["entries"], cached_entries[key]["key_entries"]

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    async def search_entries(self, search_text):
        entries, key_entries = await self.get_entries()
        result = []
        for entry in entries:
            if re.search(search_text, entry["title"]) or (entry["search_tags"] and re.search(search_text, entry["search_tags"]))\
                    or re.search(search_text, entry["markdown"]):
                result.append(entry)
        return result

    def search_tags_entries(self, entries):
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
