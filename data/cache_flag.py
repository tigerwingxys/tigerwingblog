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
# this file created at 2019.10.10

from infrastructure.utils.db_conn import DbConnect
from infrastructure.data.bases import BaseTable


class CacheFlag(BaseTable):
    def __init__(self):
        self.cached = True

    def get_cache_flag(self, cache_name, author_id=None):
        author_id = 0 if author_id is None else author_id
        return DbConnect.query_one("SELECT * FROM cache_flag WHERE cache_name = %s and author_id=%s", cache_name, author_id)

    def update_cache_flag(self, cache_name, new_time=None, author_id=None):
        author_id = 0 if author_id is None else author_id
        if new_time is not None:
            DbConnect.execute("update cache_flag set time_flag = %s where cache_name = %s and author_id=%s", new_time, cache_name, author_id)
        else:
            DbConnect.execute("update cache_flag set time_flag = current_timestamp where cache_name = %s and author_id=%s", cache_name, author_id)

    def add(self, cache_name, author_id=None, new_time=None):
        author_id = 0 if author_id is None else author_id
        if new_time is not None:
            DbConnect.execute("insert into cache_flag (cache_name, author_id, time_flag, int_flag) values (%s,%s,%s,0)", cache_name, author_id, new_time)
        else:
            DbConnect.execute("insert into cache_flag (cache_name, author_id, time_flag, int_flag) values (%s,%s,current_timestamp ,0)", cache_name, author_id)

    def delete(self, cache_name, author_id=None):
        author_id = 0 if author_id is None else author_id
        DbConnect.execute("delete from cache_flag where cache_name = %s and author_id=%s", cache_name, author_id)

