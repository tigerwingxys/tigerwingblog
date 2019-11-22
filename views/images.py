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
import io
from tornado.log import app_log
from tornado.escape import json_decode, json_encode, utf8
from views.basehandler import BaseHandler
from urllib.parse import quote
import tornado.web
import datetime
from data.cache_flag import CacheFlag
from data.author_operation import AuthorOperation
from data.entry import Entry
from infrastructure.utils.common import get_mtime,get_size
from PIL import Image

img_types = ["gif", "jpg", "jpeg", "png", "bmp"]
sort_types = {'NAME': 'shortname', 'SIZE': 'filesize', 'TYPE': 'filetype'}
cached_files = dict()
default_image_width = 800
max_image_size = 1024000


def uuid_naming_strategy(original_name):
    """File naming strategy that ignores original name and returns an UUID"""
    return str(uuid.uuid4())


class UploadHandler(BaseHandler):
    """Handle file uploads, process one single file"""

    def initialize(self, upload_path, naming_strategy):
        """Initialize with given upload path and naming strategy.
        """
        self.upload_path = upload_path
        if naming_strategy is None:
            naming_strategy = uuid_naming_strategy
        self.naming_strategy = naming_strategy

    @tornado.web.authenticated
    async def post(self, entry_id):
        author_id = str(self.current_user.id)
        upload_type = self.get_argument('dir', 'file')
        for fkey,files in self.request.files.items():
            for fileinfo in files:
                filename = fileinfo['filename']
                filename = author_id + '-' + entry_id + '~' + self.naming_strategy(filename) + '~-~' + filename
                try:
                    upload_path = os.path.join(self.upload_path, author_id, entry_id)
                    if not os.path.exists(upload_path):
                        os.makedirs(upload_path)
                    upload_path = os.path.join(upload_path, filename)

                    buffer = fileinfo['body']
                    attach_size = len(buffer)
                    if upload_type == 'image' and attach_size > 204800:
                        with io.BytesIO(buffer) as image_f:
                            with Image.open(image_f) as im:
                                width, height = im.size
                                if attach_size > max_image_size:
                                    height = int(default_image_width * (height/width))
                                    width = default_image_width
                                im.thumbnail((width, height), resample=Image.ANTIALIAS)
                                im.save(upload_path, quality=80)
                                cnt, attach_size = get_size(upload_path)
                    else:
                        with open(upload_path, 'wb') as fh:
                            fh.write(buffer)
                except IOError as e:
                    app_log.error("Failed to write file due to IOError %s", str(e))

                CacheFlag().update_cache_flag("image", author_id=author_id)
                result = {
                    "success": 1,
                    "error": 0,
                    "message": "上传成功",
                    "url": "/images/image" + filename
                }
                await AuthorOperation().add(self.current_user.id, 'upload', self.request.headers.get("X-Real-IP", ''), str(result))
                await Entry().add_attach(entry_id, attach_size)
                self.write(json_encode(result))
                return
        result = {"success": 0, "error": 1, "message": "文件上传失败"}
        self.write(json_encode(result))


class DownloadHandler(BaseHandler):

    def initialize(self, base_path):
        self.base_path = base_path

    async def get(self, filename):
        idx = filename.index('-')
        author_id = filename[:idx]
        entry_id = filename[idx+1:filename.index('~')]
        fname = filename[filename.rindex('~-~')+3:]
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % quote(fname))
        fpath = os.path.join(self.base_path, author_id, entry_id, filename)
        if os.path.exists(fpath):
            with open(fpath, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self.write(data)
            self.finish()


def get_flist(author_id, entry_id, fpath):
        global cached_files
        key = author_id+'-'+entry_id
        if key not in cached_files.keys():
            cached_files[key] = dict()
            cached_files[key]["cache_query_time"] = datetime.datetime(2000,1,1)
            cached_files[key]["rfiles"] = []

        cache_time = CacheFlag().get_cache_flag(cache_name="image", author_id=author_id)["time_flag"]
        if cached_files[key]["cache_query_time"] < cache_time:
            if os.path.exists(fpath):
                flist = os.listdir(fpath)
            else:
                flist = []
            rlist = []
            for fn in flist:
                file_ext = (fn[fn.rindex('.') + 1:]).lower()
                filename = os.path.join(fpath, fn)
                one = dict()
                one["is_dir"] = False
                one['has_file'] = False
                one['filesize'] = os.path.getsize(filename)
                one['is_photo'] = file_ext in img_types
                one['filetype'] = file_ext
                one['filename'] = fn
                one['shortname'] = fn[fn.rindex('~') + 1:]
                one['datetime'] = get_mtime(filename)
                rlist.append(one)
            cached_files[key]["rfiles"] = rlist
            cached_files[key]["cache_query_time"] = cache_time
        return cached_files[key]["rfiles"]


class BrowseHandler(BaseHandler):
    def initialize(self, base_path):
        self.base_path = base_path


    @tornado.web.authenticated
    async def get(self, entry_id):
        fpath = os.path.join(self.base_path, str(self.current_user.id), entry_id)
        rlist = get_flist(str(self.current_user.id), entry_id, fpath)
        sort_order = self.get_argument('order')

        def cmp_func(element):
            return element[sort_types[sort_order]]
        rlist.sort(key=cmp_func)
        result = dict()
        result['moveup_dir_path'] = '.'
        result['current_dir_path'] = '.'
        result['current_url'] = '/images/image'
        result['total_count'] = len(rlist)
        result['file_list'] = rlist

        self.write(json_encode(result))


class ManageHandler(BaseHandler):
    def initialize(self, base_path):
        self.base_path = base_path

    @tornado.web.authenticated
    async def get(self, entry_id):
        fpath = os.path.join(self.base_path, str(self.current_user.id), entry_id)
        rlist = get_flist(str(self.current_user.id), entry_id, fpath)
        sort_order = self.get_argument('order')

        def cmp_func(element):
            return element[sort_types[sort_order]]

        rlist.sort(key=cmp_func)
        current_url = '/images/image'

        self.render('entry_attach.html', attachments=rlist, current_url=current_url, entry_id=entry_id, orderType=sort_order)


class DeleteHandler(BaseHandler):

    def initialize(self, base_path):
        self.base_path = base_path

    @tornado.web.authenticated
    async def post(self, filename):
        idx = filename.index('-')
        author_id = filename[:idx]
        entry_id = filename[idx+1:filename.index('~')]
        fpath = os.path.join(self.base_path, author_id, entry_id, filename)
        if os.path.exists(fpath):
            fsize = os.path.getsize(fpath)
            os.remove(fpath)
            await Entry().delete_attach(entry_id, fsize)
            CacheFlag().update_cache_flag("image", author_id=author_id)

        self.redirect('/images/manage%s?order=NAME' % entry_id)
