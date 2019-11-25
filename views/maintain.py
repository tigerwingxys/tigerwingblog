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
# this file created at 2019.11.24


import os
from views.basehandler import BaseHandler
import tornado.web
import datetime
from data.author import Author
from data.backup import dump_system
from urllib.parse import quote


class BackupHandler(BaseHandler):
    def initialize(self, base_path, upload_path):
        self.base_path = base_path
        self.upload_path = upload_path

    @tornado.web.authenticated
    async def get(self, author_id, from_date, to_date):
        try:
            fromdate = datetime.datetime.strptime(from_date, '%Y%m%d%H%M%S')
            todate = datetime.datetime.strptime(to_date, '%Y%m%d%H%M%S')
        except:
            self.write('Error: date format is invalid.')
            return
        if author_id is None or len(author_id) == 0 or author_id == '0':
            if self.current_user.email != 'tigerwingxys@qq.com':
                self.write('Error: unauthorized.')
                return
            author_id = 0
        else:
            if self.current_user.email != 'tigerwingxys@qq.com' and author_id != str(self.current_user.id):
                self.write('Error: unauthorized.')
                return

        dmpauthor = Author().get(author_id)

        buf = dump_system(dmpauthor.id, dmpauthor.ident, self.upload_path, fromdate, todate)
        fname = '%d~%s-%s.blog' % (dmpauthor.id, from_date, to_date)
        # dmpfile = os.path.join(self.base_path, fname)
        # with open(dmpfile, 'wb') as f:
        #    f.write(buf)

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % quote(fname))

        self.write(buf)
        self.finish()
