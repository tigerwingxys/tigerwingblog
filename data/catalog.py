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
import datetime


cached_catalogs = dict()


class Catalog(BaseTable):
    def __init__(self):
        self.cached = True

    async def add_catalog(self, cat_id, cat_name, author_id, parent_id):
        DbConnect.execute("INSERT INTO catalogs (cat_id, cat_name, author_id, parent_id ) VALUES (%s, %s, %s, %s)",
                          cat_id, cat_name, author_id, parent_id)

    async def get_catalogs_tree(self, author_id):
        global cached_catalogs
        if author_id not in cached_catalogs.keys():
            cached_catalogs[author_id] = dict()
            cached_catalogs[author_id]["cache_query_time"] = datetime.datetime(2000, 1, 1)
            cached_catalogs[author_id]["catalogs"] = []

        cache_time = CacheFlag().get_cache_flag(cache_name="catalog")["time_flag"]
        if cached_catalogs[author_id]["cache_query_time"] < cache_time:
            rr = DbConnect.query("with RECURSIVE es as ( "
                                 "select a.cat_id,a.parent_id,a.entries_cnt,array[a.cat_id] as path from entries_statistic a where author_id=%s and parent_id=0 "
                                 "union "
                                 "select k.cat_id,k.parent_id,k.entries_cnt,c.path||k.cat_id from entries_statistic k inner join es c on c.cat_id = k.parent_id "
                                 ")select es.cat_id,es.parent_id,es.entries_cnt,cs.cat_name from es "
                                 "inner join catalogs cs on cs.cat_id=es.cat_id order by es.path", 0, None, author_id)
            cached_catalogs[author_id]["catalogs"] = rr
            cached_catalogs[author_id]["cache_query_time"] = cache_time

        return cached_catalogs[author_id]["catalogs"]
