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
# this file created at 2019.12.9

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
from tornado.web import MissingArgumentError
from tornado.escape import json_encode, json_decode
from data.author import Author
from data.entry import Entry
from data.catalog import Catalog
from data.author_operation import AuthorOperation
from views.basehandler import BaseHandler
from infrastructure.utils.common import get_text,aesencrypt
import gzip
import bson
from views.mobile_proc import process_normal, process_authenticated



class NormalHandler(BaseHandler):
    async def get(self):
        await process_normal(self, 'get')

    async def post(self):
        await process_normal(self, 'post')


class AuthenticatedHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        await process_authenticated(self, 'get')

    @tornado.web.authenticated
    async def post(self):
        await process_authenticated(self, 'post')
