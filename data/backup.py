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

from infrastructure.utils.db_conn import DbConnect
import gzip
import json
import datetime
import bson
import os
import io
import struct
from infrastructure.utils.common import aesdecrypt,aesencrypt,get_mtime


# class JsonToDatetime(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             return obj.strftime('%Y-%m-%d %H: %M: %S')
#         elif isinstance(obj, date):
#             return obj.strftime('%Y-%m-%d')
#         else:
#             return json.JSONEncoder.default(self, obj)


def backup_author_data(author, from_date, to_date):
    author['entries'] = DbConnect.query(
        'select * from entries where author_id=%s and state=1 and ((published>%s and published<%s) or (updated>%s and updated<%s))',
        0, None, author['id'], from_date, to_date, from_date, to_date)
    author['statistic'] = DbConnect.query('select * from entries_statistic where author_id=%s', 0, None, author['id'])
    author['catalogs'] = DbConnect.query('select * from catalogs where author_id =%s', 0, None, author['id'])
    author['operation'] = DbConnect.query(
        'select * from author_operation where author_id=%s and operate_date>%s and operate_date<%s', 0, None,
        author['id'], from_date, to_date)
    return author

def backup_attachments(author_id, upload_path, from_date, to_date):
    attatchs = dict()
    attatchs['author_id'] = author_id
    attatchs['entries'] = DbConnect.query(
        'select id from entries where author_id=%s and state=1 and ((published>%s and published<%s) or (updated>%s and updated<%s))',
        0, None, author_id, from_date, to_date, from_date, to_date)
    for entry in attatchs['entries']:
        fpath = os.path.join(upload_path, str(author_id), str(entry['id']))
        if os.path.exists(fpath):
            entry['files'] = dict()
            for fn in os.listdir(fpath):
                file = os.path.join(fpath, fn)
                mtime = get_mtime(file)
                if mtime < from_date.strftime('%Y-%m-%d %H:%M:%S') or mtime > to_date.strftime('%Y-%m-%d %H:%M:%S'):
                    continue
                with open(file, 'rb') as f:
                    entry['files'][fn] = f.read()

    return attatchs



def backup_dct():
    blog_sys = dict()
    blog_sys['catalogs'] = DbConnect.query('select * from catalogs where author_id = 0')
    blog_sys['cache_flag'] = DbConnect.query('select * from cache_flag')
    return blog_sys


def dump_system(author_id, ident, upload_path, from_date, to_date):
    key = ident[:16]
    iv = ident[16:32]

    buf_dct = gzip.compress(bson.dumps(backup_dct()))

    if author_id != 0:
        authors = DbConnect.query('select * from authors where id=%s', 0, None, author_id)
    else:
        authors = DbConnect.query('select * from authors')
    attachments = dict()
    all_authors = dict()
    for author in authors:
        if author['id'] == 0:
            continue
        if author['activate_state']:
            all_authors[author['id']] = backup_author_data(author, from_date, to_date)
            attachments[author['id']] = backup_attachments(author['id'], upload_path, from_date, to_date)

    buf_authors = bson.dumps(all_authors)
    buf_authors = gzip.compress(buf_authors)
    buf_authors = aesencrypt(key, iv, buf_authors)

    buf_attachs = bson.dumps(attachments)
    buf_attachs = aesencrypt(key, iv, buf_attachs)

    with io.BytesIO() as ret:
        ret.write(struct.pack('!i', len(buf_dct)))
        ret.write(buf_dct)
        ret.write(struct.pack('!i', len(buf_authors)))
        ret.write(buf_authors)
        ret.write(struct.pack('!i', len(buf_attachs)))
        ret.write(buf_attachs)
        return ret.getvalue()

def load_system(ident, buf_system):
    key = ident[:16]
    iv = ident[16:32]
    size = struct.unpack('!i', buf_system[:4])[0]
    dct = bson.loads(gzip.decompress(buf_system[4: size + 4]))
    offset = size + 4

    size = struct.unpack('!i', buf_system[offset:offset + 4])[0]
    buf_authors = buf_system[offset+4:offset+size+4]
    buf_authors = aesdecrypt(key, iv, buf_authors)
    buf_authors = gzip.decompress(buf_authors)
    authors = bson.loads(buf_authors)
    offset = offset+size+4

    size = struct.unpack('!i', buf_system[offset:offset+4])[0]
    attachments = bson.loads(aesdecrypt(key, iv, buf_system[offset+4:offset+size+4]))

    return dct, authors, attachments
