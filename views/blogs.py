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

import bcrypt
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
from tornado.web import MissingArgumentError
from tornado.escape import json_encode, json_decode
from infrastructure.utils.db_conn import NoResultError,begin_transaction,commit_transaction,rollback_transaction
from data.author import Author
from data.entry import Entry
from data.catalog import Catalog
from business.author_process import check_password

DEFAULT_FETCH_SIZE = 10
DEFAULT_CONTENT_URL = "/blog/archive0-%d" % DEFAULT_FETCH_SIZE


def get_authorname_by_id(author_id):
    author = Author().get_author_by_id(author_id)
    name = author_id
    if author is not None:
        name = author.name
    return name


class BaseHandler(tornado.web.RequestHandler):
    async def prepare(self):
        # get_current_user cannot be a coroutine, so set
        # self.current_user in prepare instead.
        user_id = self.get_secure_cookie("tigerwingblog")
        if user_id:
            self.current_user = await Author().get_author(int(user_id))

    def any_author_exists(self):
        return True


class HomeHandler(BaseHandler):
    async def get(self):
        try:
            goto = self.get_argument("goto")
            goto_url = "/blog/entry/"+goto
        except MissingArgumentError:
            goto_url = DEFAULT_CONTENT_URL
        self.render("base.html", content_url=goto_url, get_authorname_by_id=get_authorname_by_id)


class ShareEntryHandler(BaseHandler):
    async def get(self, content_url):
        goto_url = "/blog/entry/"+content_url
        self.render("base.html", content_url=goto_url, get_authorname_by_id=get_authorname_by_id)

class MyBlogHandler(BaseHandler):
    async def get(self,offset, fetch_size, cat_id):
        user_id = self.current_user.id
        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        origin_entries, key_entries = await Entry().get_entries_by_author(user_id, cat_id)
        try:
            tag_key = self.get_argument("tag_key")
        except MissingArgumentError:
            tag_key = ""
        entries = key_entries[tag_key] if len(tag_key) != 0 else origin_entries
        entry_cnt = len(entries)
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
                url = "/blog/myblogs%d-%d/%s" % (ipage, fetch_size, cat_id)
                pages.append({"url": url+url_suffix, "page_title": str(ipage)})
                i = i+1
        if len(tag_key) == 0:
            url = "/blog/myblogs0-%d/%s?tag_key=" % (fetch_size, cat_id)
            for key in key_entries.keys():
                cnt = len(key_entries[key])
                tt = "%s(%d)" % (key, cnt)
                pages.append({"url": url + key, "page_title": tt})
        part_entries = entries[offset:offset+fetch_size]
        self.render("archive.html", entries=part_entries, pages=pages, current_page=str(offset), get_authorname_by_id=get_authorname_by_id)


class MyBlogTreeHandler(BaseHandler):
    def check_xsrf_cookie(self) -> None:
        pass

    async def post(self):
        user_id = None
        if self.current_user is not None:
            user_id = self.current_user.id
        cats = await Catalog().get_catalogs_tree(author_id=user_id)

        result = []
        base_url = "/blog/myblogs0-%d/" % DEFAULT_FETCH_SIZE
        result.append({"id": 0, "pId": -1, "open": "true", "name": "根文件夹", "entry_url": base_url})
        for row in cats:
            cnt = row["entries_cnt"]
            cname = row["cat_name"] + ("(%d)" % cnt)
            if cnt > 0:
                result.append({"id": row["cat_id"], "pId": row["parent_id"], "open": "true", "click": "true", "name": cname, "entry_url": (base_url + str(row["cat_id"]))})
            else:
                result.append({"id": row["cat_id"], "pId": row["parent_id"], "open": "true", "name": cname})
        self.write(json_encode(result))


class blogEntryHandler(BaseHandler):
    async def get(self, slug):
        entry = await Entry().get_entry(slug=slug)
        if not entry:
            raise tornado.web.HTTPError(404)
        self.render("entry.html", entry=entry)


class blogRefreshEntryHandler(BaseHandler):
    async def get(self, slug):
        goto_url = "/?goto="+slug
        self.render("login_ok.html", goto_url=goto_url)


class ArchiveHandler(BaseHandler):
    async def get(self, offset, fetch_size):
        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        origin_entries, key_entries = await Entry().get_entries()
        try:
            tag_key = self.get_argument("tag_key")
        except MissingArgumentError:
            tag_key = ""
        entries = key_entries[tag_key] if len(tag_key) != 0 else origin_entries
        entry_cnt = len(entries)
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
                url = "/blog/archive%d-%d" % (ipage, fetch_size)
                pages.append({"url": url+url_suffix, "page_title": str(ipage)})
                i = i+1
        if len(tag_key) == 0:
            url = "/blog/archive0-%d?tag_key=" % fetch_size
            for key in key_entries.keys():
                cnt = len(key_entries[key])
                tt = "%s(%d)" % (key, cnt)
                pages.append({"url": url + key, "page_title": tt})
        part_entries = entries[offset:offset+fetch_size]
        self.render("archive.html", entries=part_entries, pages=pages, current_page=str(offset), get_authorname_by_id=get_authorname_by_id)


class SearchHandler(BaseHandler):
    async def get(self, offset, fetch_size, search_text):
        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        entries = await Entry().search_entries(search_text)
        entry_cnt = len(entries)
        page_cnt = int(entry_cnt/fetch_size)
        if (entry_cnt % fetch_size) > 0:
            page_cnt += 1
        i = 0
        pages = []
        if page_cnt > 1:
            while i < page_cnt:
                ipage = i*fetch_size
                url = "/blog/search%d-%d/" % (ipage,fetch_size)
                url = url + search_text
                pages.append({"url": url, "page_title": str(ipage)})
                i = i+1
        part_entries = entries[offset:offset+fetch_size]
        self.render("archive.html", entries=part_entries, pages=pages, current_page=offset, get_authorname_by_id=get_authorname_by_id)


class FeedHandler(BaseHandler):
    async def get(self):
        entries, key_entries = await Entry().get_entries(fetch_size=10)
        self.set_header("Content-Type", "application/atom+xml")
        self.render("feed.xml", entries=entries)


class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, cat_id):
        entry_id = self.get_argument("id", None)
        entry = None
        if entry_id:
            entry = await Entry().get_entry(entry_id=entry_id)
        self.render("compose.html", entry=entry, cat_id=cat_id)

    @tornado.web.authenticated
    async def post(self, cat_id):
        entry_id = self.get_argument("id", None)
        title = self.get_argument("title")
        text = self.get_argument("content-editormd-markdown-doc")
        html = self.get_argument("content-editormd-html-code")
        search_tags = self.get_argument("search_tags")
        # cat_id = int(self.get_argument("cat_id"))
        try:
            is_public = bool(self.get_argument("is_public"))
        except MissingArgumentError:
            is_public = False
        try:
            is_encrypt = bool(self.get_argument("is_encrypt"))
        except MissingArgumentError:
            is_encrypt = False
        # html = markdown.markdown(text)
        if entry_id:
            entry = await Entry().update_entry(entry_id, title, text, html, is_public, is_encrypt, search_tags, cat_id)
            slug = entry.slug
        else:
            slug = await Entry().add_entry(self.current_user, title, text, html, is_public, is_encrypt, search_tags, cat_id)
        self.redirect("/blog/refresh/" + slug)

class CatalogHandler(BaseHandler):
    def check_xsrf_cookie(self) -> None:
        pass

    async def post(self):
        args = json_decode(self.request.body)
        method = args.get('method')
        if method == 'add':
            rr = await Catalog().add_catalog(args.get("cat_id"), args.get("cat_name"), self.current_user.id, args.get("parent_id"))
            if rr:
                result = {"success": 1, "message": "节点%s[%s]添加成功!" % (args.get('cat_name'), args.get('cat_id'))}
            else:
                result = {"success": 0, "message": "节点%s[%s]添加失败!" % (args.get('cat_name'), args.get('cat_id'))}
            self.write(json_encode(result))
        elif method == 'modify':
            rr = await Catalog().modify_catalog(args.get("cat_id"), args.get("cat_name"))
            if rr:
                result = {"success": 1, "message": "节点%s[%s]修改成功!" % (args.get('cat_name'), args.get('cat_id'))}
            else:
                result = {"success": 0, "message": "节点%s[%s]修改失败!" % (args.get('cat_name'), args.get('cat_id'))}
            self.write(json_encode(result))
        elif method == 'delete':
            rr = await Catalog().delete_catalog(args.get("cat_id"), self.current_user.id)
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

class AuthCreateHandler(BaseHandler):
    def get(self):
        self.render("create_author.html")

    async def post(self):
        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(self.get_argument("password")),
            bcrypt.gensalt(),
        )
        hashed_password = tornado.escape.to_unicode(hashed_password)
        author = await Author().add_author(self.get_argument("email"), self.get_argument("name"), hashed_password, )
        self.set_secure_cookie("tigerwingblog", str(author.id))
        self.redirect(self.get_argument("next", "/"))


class AuthLoginHandler(BaseHandler):
    async def get(self):
        # If there are no authors, redirect to the account creation page.
        if not self.any_author_exists():
            self.redirect("/auth/create")
        else:
            self.render("login.html", error=None)

    async def post(self):
        try:
            author = await Author().get_author_by_email( self.get_argument("email"))
        except NoResultError:
            self.render("login.html", error="email not found")
            return
        if await check_password(self.get_argument("password"), author.hashed_password):
            self.set_secure_cookie("tigerwingblog", str(author.id))
            self.render("login_ok.html", goto_url="/")
        else:
            self.render("login.html", error="incorrect password")


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("tigerwingblog")
        self.redirect(self.get_argument("next", "/"))


class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry, get_authorname_by_id=get_authorname_by_id)
