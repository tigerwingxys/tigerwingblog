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
# this file created at 2019.11.11

from infrastructure.utils.db_conn import DbConnect
from infrastructure.data.bases import BaseTable


class EntriesStatistic(BaseTable):
    def __init__(self):
        self.cached = True

    def add(self, author_id, cat_id, parent_id):
        DbConnect.execute("insert into entries_statistic (author_id,cat_id,parent_id) values (%s,%s,%s)",
                          author_id, cat_id, parent_id)

    def add_system_cats(self, author_id):
        DbConnect.execute("insert into entries_statistic(author_id,cat_id,parent_id) select %s,cat_id,parent_id from catalogs where author_id=0",
                          author_id)

    def delete(self, author_id, cat_id):
        DbConnect.execute("delete from entries_statistic where author_id=%s and cat_id=%s",
                          author_id, cat_id)

    def delete_by_author(self, author_id):
        DbConnect.execute("delete from entries_statistic where author_id=%s ", author_id)

    def plus_one(self, author_id, cat_id):
        DbConnect.execute("update entries_statistic set entries_cnt = entries_cnt +1 where author_id=%s and cat_id=%s",
                          author_id, cat_id)

    def minus_one(self, author_id, cat_id):
        DbConnect.execute("update entries_statistic set entries_cnt = entries_cnt -1 where author_id=%s and cat_id=%s",
                          author_id, cat_id)
