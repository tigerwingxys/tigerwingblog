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
# this file created at 2019.11.17

from infrastructure.utils.db_conn import DbConnect
from infrastructure.data.bases import BaseTable


class AuthorOperation(BaseTable):
    def __init__(self):
        self.cached = False

    async def add(self, author_id, operate, remote_ip, info='{}'):
        DbConnect.execute("INSERT INTO author_operation(author_id, operate, remote_ip, info) "
            "VALUES (%s, %s, %s, %s) ", author_id, operate, remote_ip, info)
