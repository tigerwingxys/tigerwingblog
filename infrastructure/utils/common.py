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
# this file created at 2019.11.19

import os
import re
import time
from Crypto.Cipher import AES

def get_size( file_path ):
    if not os.path.exists(file_path):
        return 0, 0
    elif os.path.isfile(file_path):
        return 1, os.path.getsize(file_path)
    else:
        size = 0
        total_cnt = 0
        for f in (os.listdir(file_path)):
            cnt, fsize = get_size(os.path.join(file_path, f))
            size += fsize
            total_cnt += cnt
        return total_cnt, size


def get_text(html):
    text = re.sub(r'<head.*?>.*?</head>', '', html, flags=re.M | re.S | re.I)
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.M | re.S | re.I)
    text = re.sub('<.*?>', '', text, flags=re.M | re.S)
    text = re.sub(r'\s*\n', '\n', text, flags=re.M | re.S)
    return text

def get_mtime(filename):
    t = os.path.getmtime(filename)
    tt = time.localtime(t)
    return time.strftime('%Y-%m-%d %H:%M:%S', tt)


def aesencrypt(key, iv, data):
    if isinstance(key, str):
        key = bytes(key, 'utf-8')
    if isinstance(iv, str):
        iv = bytes(iv, 'utf-8')
    aes = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)

    size = len(data)
    ladd = 16 - (size % 16)
    data = data + (chr(ladd).encode('utf-8') * ladd)
    return aes.encrypt(data)


def aesdecrypt(key, iv, data):
    if isinstance(key, str):
        key = bytes(key, 'utf-8')
    if isinstance(iv, str):
        iv = bytes(iv, 'utf-8')
    aes = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    buf = aes.decrypt(data)
    return buf[:-buf[-1]]
