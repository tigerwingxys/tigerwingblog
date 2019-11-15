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
# this file created at 2019.9.10


import uuid
import os
from tornado.log import app_log
from tornado.escape import json_decode, json_encode, utf8
from views.basehandler import BaseHandler
from urllib.parse import quote


def uuid_naming_strategy(original_name):
    """File naming strategy that ignores original name and returns an UUID"""
    return str(uuid.uuid4())


class UploadHandler(BaseHandler):
    """Handle file uploads."""

    def initialize(self, upload_path, naming_strategy):
        """Initialize with given upload path and naming strategy.
        :keyword upload_path: The upload path.
        :type upload_path: str
        :keyword naming_strategy: File naming strategy.
        :type naming_strategy: (str) -> str function
        """
        self.upload_path = upload_path
        if naming_strategy is None:
            naming_strategy = uuid_naming_strategy
        self.naming_strategy = naming_strategy
        app_log.info('UploadHandler initialize.')

    def post(self):
        author_id = "%d" % self.current_user.id
        for fkey,files in self.request.files.items():
            for fileinfo in files:
                filename = fileinfo['filename']  # self.naming_strategy(fileinfo['filename'])
                filename = author_id + '-' + self.naming_strategy(filename) + '-' + filename
                try:
                    upload_path = os.path.join(self.upload_path, author_id)
                    if not os.path.exists(upload_path):
                        os.makedirs(upload_path)
                    upload_path = os.path.join(upload_path, filename)
                    with open(upload_path, 'wb') as fh:
                        fh.write(fileinfo['body'])
                    app_log.info("%s uploaded %s, saved as %s",
                                 str(self.request.remote_ip),
                                 str(fileinfo['filename']),
                                 filename)
                except IOError as e:
                    app_log.error("Failed to write file due to IOError %s", str(e))
        result = {
            "success": 1,
            "message": "上传成功",
            "url": "/images/image" + filename
        }
        self.write(json_encode(result))


class DownloadHandler(BaseHandler):

    def initialize(self, base_path):
        self.base_path = base_path

    def get(self, filename):
        ss = filename[:filename.index('-')]
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % quote(filename))
        fpath = os.path.join(self.base_path, ss, filename)
        with open(fpath, 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                self.write(data)
        self.finish()

