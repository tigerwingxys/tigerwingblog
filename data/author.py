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


class Author(BaseTable):
    def __init__(self):
        self.cached = True

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    async def get_author(self, author_id):
        return DbConnect.query_one("SELECT * FROM authors WHERE id = %s", int(author_id))

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    def get_author_by_id(self, author_id):
        return DbConnect.query_one("SELECT * FROM authors WHERE id = %s", int(author_id))

    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    async def get_author_by_email(self, email):
        return DbConnect.query_one("select * from authors where email = %s", email, )

    async def add_author(self, email, name, upassword):
        return DbConnect.query_one(
            "INSERT INTO authors (email, name, hashed_password) "
            "VALUES (%s, %s, %s) RETURNING id", email, name, upassword,)
