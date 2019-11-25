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

DEFAULT_FETCH_SIZE = 10
DEFAULT_CONTENT_URL = "/blog/archive0-%d" % DEFAULT_FETCH_SIZE


def get_authorname_by_id(author_id):
    author = Author().get(author_id)
    name = author_id
    if author is not None:
        name = author.name
    return name



class HomeHandler(BaseHandler):
    async def get(self):
        goto = self.get_argument("goto", None)
        if goto:
            goto_url = goto
        elif self.current_user:
            goto_url = '/blog/myblogs0-10/'
        else:
            goto_url = DEFAULT_CONTENT_URL
        self.render("base.html", content_url=goto_url, get_authorname_by_id=get_authorname_by_id)


class ShareEntryHandler(BaseHandler):
    async def get(self, content_url):
        goto_url = "/blog/entry/"+content_url
        self.render("base.html", content_url=goto_url, get_authorname_by_id=get_authorname_by_id)

class MyBlogHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, offset, fetch_size, cat_id):
        user_id = self.current_user.id
        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        origin_entries, key_entries = await Entry().get_entries_by_author(user_id, cat_id)
        tag_key = self.get_argument("tag_key", "")
        entries = key_entries[tag_key] if len(tag_key) != 0 else origin_entries
        entry_cnt = len(entries)
        page_cnt = int(entry_cnt/fetch_size)
        if (entry_cnt % fetch_size) > 0:
            page_cnt += 1
        i = 0
        pages = []
        navigation = []
        search_index = []
        url_suffix = ""
        navigation.append({'url': '/blog/myblogs0-%d/' % fetch_size, 'page_title': '根文件夹' + ('' if len(cat_id)>1 else '(%d)' % len(origin_entries))})
        if len(cat_id)>0 and cat_id != '0':
            navigation.append({'url': '/blog/myblogs0-%d/%s' % (fetch_size, cat_id), 'page_title': '%s(%d)' % ((Catalog().get(user_id, cat_id)).cat_name, len(origin_entries))})
        if len(tag_key) > 0:
            navigation.append({"url": "#", "page_title": '%s(%d)' % (tag_key, entry_cnt)})
            url_suffix = "?tag_key="+tag_key
        if page_cnt > 1:
            while i < page_cnt:
                ipage = i*fetch_size
                url = "/blog/myblogs%d-%d/%s" % (ipage, fetch_size, cat_id)
                pages.append({"url": url+url_suffix, "page_title": str(ipage)})
                i = i+1
        if len(tag_key) == 0:
            url = "/blog/myblogs0-%d/%s?tag_key=" % (fetch_size, cat_id)
            for key in key_entries.keys():
                cnt = len(key_entries[key])
                tt = "%s(%d)" % (key, cnt)
                search_index.append({"url": url + key, "page_title": tt})
        part_entries = entries[offset:offset+fetch_size]

        self.render("archive.html", entries=part_entries, pages=pages, navigation=navigation, search_index=search_index, current_page=str(offset),
                    get_authorname_by_id=get_authorname_by_id, quota=True, get_text=get_text, search_text=None)


class MyBlogTreeHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        user_id = None
        if self.current_user is not None:
            user_id = self.current_user.id
        cats = await Catalog().get_catalogs_tree(author_id=user_id)

        result = []
        base_url = "/blog/myblogs0-%d/" % DEFAULT_FETCH_SIZE
        result.append({"id": 0, "pId": -1, "open": "true", "name": "根文件夹", "entry_url": base_url})
        total = 0
        for row in cats:
            cnt = row["entries_cnt"]
            total += cnt
            cname = row["cat_name"] + ("(%d)" % cnt)
            result.append({"id": row["cat_id"], "pId": row["parent_id"], "open": "true", "click": "true", "name": cname, "entry_url": (base_url + str(row["cat_id"]))})
        result[0]['name'] = '根文件夹(%d)' % total
        self.write(json_encode(result))


class blogEntryHandler(BaseHandler):
    async def get(self, slug):
        entry = await Entry().get(slug=slug)
        if not entry:
            raise tornado.web.HTTPError(404)
        self.render("entry.html", entry=entry)


class blogRefreshEntryHandler(BaseHandler):
    async def get(self, slug):
        goto_url = "/?goto=/blog/entry/"+slug
        self.render("login_ok.html", goto_url=goto_url, message='ok', delay=1)


class ArchiveHandler(BaseHandler):
    async def get(self, offset, fetch_size):
        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        origin_entries, key_entries = await Entry().get_shared()
        tag_key = self.get_argument("tag_key", "")
        entries = key_entries[tag_key] if len(tag_key) != 0 else origin_entries
        entry_cnt = len(entries)
        page_cnt = int(entry_cnt/fetch_size)
        if (entry_cnt % fetch_size) > 0:
            page_cnt += 1
        i = 0
        pages = []
        navigation = []
        search_index = []
        url_suffix = ""
        navigation.append({'url': '/blog/archive0-%d' % fetch_size, 'page_title': '网站最新分享文章(%d)' % len(origin_entries)})
        if len(tag_key) > 0:
            navigation.append({"url": "#", "page_title": '%s(%d)' % (tag_key, entry_cnt)})
            url_suffix = "?tag_key="+tag_key
        if page_cnt > 1:
            while i < page_cnt:
                ipage = i*fetch_size
                url = "/blog/archive%d-%d" % (ipage, fetch_size)
                pages.append({"url": url+url_suffix, "page_title": str(ipage)})
                i = i+1
        if len(tag_key) == 0:
            url = "/blog/archive0-%d?tag_key=" % fetch_size
            for key in key_entries.keys():
                cnt = len(key_entries[key])
                tt = "%s(%d)" % (key, cnt)
                search_index.append({"url": url + key, "page_title": tt})
        part_entries = entries[offset:offset+fetch_size]
        self.render("archive.html", entries=part_entries, pages=pages, navigation=navigation, search_index=search_index, current_page=str(offset),
                    get_authorname_by_id=get_authorname_by_id, quota=False, get_text=get_text, search_text=None)


class ManageHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, offset, fetch_size):
        ss = dict()
        rr = await Entry().get_usage_by_author(self.current_user.id)
        ss['attach_usage'] = '%.2fKB' % (rr.attach_usage/1024)
        ss['usage'] = '%.2fKB' % ((rr.attach_usage+rr.txt_usage)/1024)

        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        origin_entries, key_entries = await Entry().get_entries_by_author(self.current_user.id)
        tag_key = self.get_argument("tag_key", "")
        entries = key_entries[tag_key] if len(tag_key) != 0 else origin_entries
        entry_cnt = len(entries)
        ss['entries_cnt'] = entry_cnt
        page_cnt = int(entry_cnt/fetch_size)
        if (entry_cnt % fetch_size) > 0:
            page_cnt += 1
        i = 0
        pages = []
        url_suffix = ""
        if len(tag_key) > 0:
            pages.append({"url": "#", "page_title": tag_key})
            url_suffix = "?tag_key="+tag_key
        if page_cnt > 1:
            while i < page_cnt:
                ipage = i*fetch_size
                url = "/blog/manage%d-%d" % (ipage, fetch_size)
                pages.append({"url": url+url_suffix, "page_title": str(ipage)})
                i = i+1
        if len(tag_key) == 0:
            url = "/blog/archive0-%d?tag_key=" % fetch_size
            for key in key_entries.keys():
                cnt = len(key_entries[key])
                tt = "%s(%d)" % (key, cnt)
                pages.append({"url": url + key, "page_title": tt})
        part_entries = entries[offset:offset+fetch_size]
        self.render("manage_entries.html", entries=part_entries, pages=pages, current_page=str(offset),
                    get_authorname_by_id=get_authorname_by_id, quota=False, get_text=get_text, usage=ss)


class SearchHandler(BaseHandler):
    async def get(self, offset, fetch_size, search_text):
        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        author_id = None
        if self.current_user is not None:
            author_id = self.current_user.id
        entries = await Entry().search(search_text, author_id)
        entry_cnt = len(entries)
        page_cnt = int(entry_cnt/fetch_size)
        if (entry_cnt % fetch_size) > 0:
            page_cnt += 1
        i = 0
        pages = list()
        navigation = list()
        navigation.append({'url': '', 'page_title': '[%s]搜索结果(%d)' % (search_text, len(entries))})
        if page_cnt > 1:
            while i < page_cnt:
                ipage = i*fetch_size
                url = "/blog/search%d-%d/" % (ipage, fetch_size)
                url = url + search_text
                pages.append({"url": url, "page_title": str(ipage)})
                i = i+1
        part_entries = entries[offset:offset+fetch_size]
        self.render("archive.html", entries=part_entries, pages=pages, navigation=navigation, search_index=[], current_page=str(offset),
                    get_authorname_by_id=get_authorname_by_id, quota=False, get_text=get_text, search_text=search_text)


class FeedHandler(BaseHandler):
    async def get(self):
        entries, key_entries = await Entry().get_shared(fetch_size=10)
        self.set_header("Content-Type", "application/atom+xml")
        self.render("feed.xml", entries=entries)


compose_editor = {"kind-editor": "compose_kindedit.html", "editor.md": "compose_editormd.html"}
one_MB = 1024*1024

class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, cat_id):
        ss = eval(self.current_user.settings)
        editor = ss["default-editor"]

        entry_id = self.get_argument("id", None)
        if entry_id:
            entry = await Entry().get(entry_id=entry_id)
            editor = entry.editor
        else:
            rr = await Entry().get_usage_by_author(self.current_user.id)
            if rr.txt_usage:
                usage = rr.attach_usage + rr.txt_usage
            else:
                usage = 0
            if usage >= self.current_user.quota * one_MB:
                message = '您的空间限额为%dMB，您当前已经使用%.2fMB，2秒后自动跳转到使用空间管理……' % \
                          (self.current_user.quota, usage/one_MB)
                self.render("login_ok.html", message=message, goto_url="/?goto=/blog/manage0-10", delay=2000)
                return

            entry = await Entry().get_empty_entry(author_id=self.current_user.id, cat_id=cat_id, editor=editor)

        self.render(compose_editor[editor], entry=entry, cat_id=cat_id)

    @tornado.web.authenticated
    async def post(self, cat_id):
        entry_id = self.get_argument("id")
        title = self.get_argument("title")
        text = self.get_argument("content-editormd-markdown-doc", "")
        html = self.get_argument("content-editormd-html-code", "")
        editor = self.get_argument("editor")
        if len(html) == 0:
            html = text
        if editor == 'kind-editor':
            html = text
            text = ''

        search_tags = self.get_argument("search_tags")
        try:
            is_public = self.get_argument("is_public")
        except MissingArgumentError:
            is_public = False
        else:
            is_public = True
        try:
            is_encrypt = self.get_argument("is_encrypt")
        except MissingArgumentError:
            is_encrypt = False
        else:
            is_encrypt = True
        if await Entry().is_exists(entry_id=entry_id):
            old_entry = await Entry().get(entry_id=entry_id)
            await Entry().update(self.current_user, entry_id, title, text, html, is_public, is_encrypt, search_tags, cat_id)
            slug = old_entry.slug
            data = gzip.compress(bson.dumps(old_entry))
            await AuthorOperation().add(self.current_user.id, 'update_entry', self.request.headers.get("X-Real-IP", '') or self.request.remote_ip, info=str({"entry_id": entry_id}), data=data)
        else:
            slug = await Entry().add_entry(self.current_user, entry_id, title, text, html, is_public, is_encrypt, search_tags, cat_id)
            await AuthorOperation().add(self.current_user.id, 'add_entry', self.request.headers.get("X-Real-IP", '') or self.request.remote_ip, str({"entry_id": entry_id}))
        self.redirect("/blog/refresh/" + slug)


class DeleteHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, cat_id):
        entry_id = self.get_argument('id', '')
        entry = await Entry().get(entry_id=entry_id)
        if not entry:
            raise tornado.web.HTTPError(404)
        self.render('delete.html', entry=entry)

    @tornado.web.authenticated
    async def post(self, cat_id):
        entry_id = self.get_argument('id', '')

        await Entry().delete(self.current_user.id, entry_id, cat_id)
        await AuthorOperation().add(self.current_user.id, 'delete_entry', self.request.headers.get('X-Real-IP', '') or self.request.remote_ip, str({'entry_id': entry_id}))
        self.render("login_ok.html", message="文章已经删除，自动跳转到主页", goto_url="/", delay=1000)

class CatalogHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        args = json_decode(self.request.body)
        method = args.get('method')
        if method == 'add':
            rr = await Catalog().add(args.get("cat_id"), args.get("cat_name"), self.current_user.id, args.get("parent_id"))
            if rr:
                result = {"success": 1, "message": "节点%s[%s]添加成功!" % (args.get('cat_name'), args.get('cat_id'))}
            else:
                result = {"success": 0, "message": "节点%s[%s]添加失败!" % (args.get('cat_name'), args.get('cat_id'))}
            self.write(json_encode(result))
        elif method == 'modify':
            rr = await Catalog().modify(args.get("cat_id"), args.get("cat_name"), self.current_user.id)
            if rr:
                result = {"success": 1, "message": "节点%s[%s]修改成功!" % (args.get('cat_name'), args.get('cat_id'))}
            else:
                result = {"success": 0, "message": "节点%s[%s]修改失败!" % (args.get('cat_name'), args.get('cat_id'))}
            self.write(json_encode(result))
        elif method == 'delete':
            rr = await Catalog().delete(args.get("cat_id"), self.current_user.id)
            if rr:
                result = {"success": 1, "message": "节点[%s]删除成功!" % args.get('cat_id')}
            else:
                result = {"success": 0, "message": "节点[%s]删除失败!" % args.get('cat_id')}
            self.write(json_encode(result))
        else:
            result = {
                "success": 0,
                "message": "方法[%s]没有定义!" % method
            }
            self.write(json_encode(result))
        await AuthorOperation().add(self.current_user.id, 'catalog', self.request.headers.get("X-Real-IP", ''), str(result))


class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry, get_authorname_by_id=get_authorname_by_id)
