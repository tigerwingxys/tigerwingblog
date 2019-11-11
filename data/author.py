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

from infrastructure.utils.db_conn import DbConnect
from infrastructure.data.bases import BaseTable
from cachetools import cached, TTLCache
from data.entries_statistic import EntriesStatistic
from data.cache_flag import CacheFlag


class Author(BaseTable):
    def __init__(self):
        self.cached = True

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    def get_author(self, author_id):
        return DbConnect.query_one("SELECT * FROM authors WHERE id = %s", author_id)

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    async def get_author_by_email(self, email):
        return DbConnect.query_one("select * from authors where email = %s", email, )

    async def add_author(self, email, name, upassword, key):
        author = DbConnect.execute_returning( "INSERT INTO authors (email, name, hashed_password, activate_key) "
            "VALUES (%s, %s, %s, %s) RETURNING *", email, name, upassword, key)
        EntriesStatistic().add_system_cats(author.id)
        CacheFlag().add("catalog", author_id=author.id, new_time=author.create_date)
        return author

    async def activate_author(self, author_id):
        return DbConnect.execute("update authors set activate_state='true' where id = %s", author_id)

    async def del_author(self, author_id):
        EntriesStatistic().delete_by_author(author_id)
        DbConnect.execute("delete from authors where id=%s and id!=0 ", author_id)
        CacheFlag().delete("catalog", author_id=author_id)
