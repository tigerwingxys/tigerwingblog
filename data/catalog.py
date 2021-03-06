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
# this file created at 2019.10.30

from infrastructure.utils.db_conn import DbConnect
from infrastructure.data.bases import BaseTable
from data.cache_flag import CacheFlag
from data.entries_statistic import EntriesStatistic
import datetime
from cachetools import cached, TTLCache

cached_catalogs = dict()


class Catalog(BaseTable):
    def __init__(self):
        self.cached = True

    async def add(self, cat_id, cat_name, author_id, parent_id):
        rr = DbConnect.execute_returning("INSERT INTO catalogs (cat_id, cat_name, author_id, parent_id ) VALUES (%s, %s, %s, %s) returning *",
                          cat_id, cat_name, author_id, parent_id)
        CacheFlag().update_cache_flag("catalog", new_time=rr.create_date, author_id=author_id)
        EntriesStatistic().add(author_id,cat_id,parent_id)
        return rr

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    def get(self, author_id, cat_id):
        return DbConnect.query_one("SELECT * FROM catalogs WHERE cat_id = %s and author_id in(0,%s)", cat_id, author_id)

    async def modify(self, cat_id, cat_name, author_id):
        DbConnect.execute("update catalogs set cat_name=%s where cat_id=%s and author_id=%s", cat_name, cat_id, author_id)
        CacheFlag().update_cache_flag("catalog", author_id=author_id)
        return True

    async def delete(self, cat_id, author_id):
        es = DbConnect.query_one("select * from entries_statistic where cat_id=%s and author_id=%s",cat_id, author_id)
        if es["entries_cnt"] > 0:
            return False
        EntriesStatistic().delete(author_id, cat_id)
        DbConnect.execute("delete from catalogs where cat_id=%s and author_id=%s", cat_id, author_id)
        CacheFlag().update_cache_flag("catalog", author_id=author_id)
        return True

    async def get_catalogs_tree(self, author_id):
        global cached_catalogs
        if author_id not in cached_catalogs.keys():
            cached_catalogs[author_id] = dict()
            cached_catalogs[author_id]["cache_query_time"] = datetime.datetime(2000, 1, 1)
            cached_catalogs[author_id]["catalogs"] = []

        cache_time = CacheFlag().get_cache_flag(cache_name="catalog", author_id=author_id)["time_flag"]
        if cached_catalogs[author_id]["cache_query_time"] < cache_time:
            rr = DbConnect.query("with RECURSIVE es as ( "
                                 "select a.cat_id,a.parent_id,a.entries_cnt,array[a.cat_id] as path,a.author_id from entries_statistic a where author_id=%s and parent_id=0 "
                                 "union "
                                 "select k.cat_id,k.parent_id,k.entries_cnt,c.path||k.cat_id,k.author_id from entries_statistic k inner join es c on c.cat_id = k.parent_id "
                                 " and c.author_id=k.author_id)select es.cat_id,es.parent_id,es.entries_cnt,cs.cat_name,es.author_id from es "
                                 "inner join catalogs cs on cs.cat_id=es.cat_id and cs.author_id in (es.author_id,0) order by es.path", 0, None, author_id)
            cached_catalogs[author_id]["catalogs"] = rr
            cached_catalogs[author_id]["cache_query_time"] = cache_time

        return cached_catalogs[author_id]["catalogs"]
