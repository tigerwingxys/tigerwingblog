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
from tornado.escape import json_encode
from infrastructure.utils.db_conn import NoResultError,begin_transaction,commit_transaction
from data.author import Author
from data.entry import Entry
from business.author_process import check_password

DEFAULT_FETCH_SIZE = 10
DEFAULT_CONTENT_URL = "/blog/archive0-10"


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
        user_id = self.get_secure_cookie("tigerblog")
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
    async def get(self,offset, fetch_size):
        user_id = None
        if self.current_user is not None:
            user_id = self.current_user.id

        offset = int(offset)
        fetch_size = int(fetch_size)
        if fetch_size is None or fetch_size == 0:
            fetch_size = DEFAULT_FETCH_SIZE
        entries = await Entry().get_entries_by_author(user_id)
        entry_cnt = len(entries)
        page_cnt = int(entry_cnt/fetch_size)
        if (entry_cnt % fetch_size) > 0:
            page_cnt += 1
        i = 0
        pages = []
        if page_cnt > 1:
            while i < page_cnt:
                ipage = i*fetch_size
                url = "/blog/myblogs%d-%d" % (ipage, fetch_size)
                pages.append({"url": url, "page_title": str(ipage)})
                i = i+1
        part_entries = entries[offset:offset+fetch_size]
        self.render("archive.html", entries=part_entries, pages=pages, current_page=offset, get_authorname_by_id=get_authorname_by_id)


class MyBlogTreeHandler(BaseHandler):
    def check_xsrf_cookie(self) -> None:
        pass

    async def post(self):
        user_id = None
        if self.current_user is not None:
            user_id = self.current_user.id
        entries = await Entry().get_entries_by_author(user_id)
        current_month = "0"
        result = []
        tid = 0
        pid = 0
        i = 0
        opened = False
        for row in entries:
            if row["published"].strftime("%Y-%m") != current_month:
                current_month = row["published"].strftime("%Y-%m")
                tid += 1
                pid = tid
                i = 0
                if not opened:
                    opened = True
                    result.append({"id": tid, "pId": 0, "name": current_month,  "open": "true", "click": "false"})
                else:
                    result.append({"id": tid, "pId": 0, "name": current_month,  "click": "false"})
            result.append({"id": tid*100+i, "pId": pid, "name": row["title"], "entry_url": "/blog/entry/" + row["slug"]})
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
        entries = await Entry().get_entries()
        entry_cnt = len(entries)
        page_cnt = int(entry_cnt/fetch_size)
        if (entry_cnt % fetch_size) > 0:
            page_cnt += 1
        i = 0
        pages = []
        if page_cnt > 1:
            while i < page_cnt:
                ipage = i*fetch_size
                url = "/blog/archive%d-%d" % (ipage, fetch_size)
                pages.append({"url": url, "page_title": str(ipage)})
                i = i+1
        part_entries = entries[offset:offset+fetch_size]
        self.render("archive.html", entries=part_entries, pages=pages, current_page=offset, get_authorname_by_id=get_authorname_by_id)


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
        entries = await Entry().get_entries(fetch_size=10)
        self.set_header("Content-Type", "application/atom+xml")
        self.render("feed.xml", entries=entries)


class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        entry_id = self.get_argument("id", None)
        entry = None
        if entry_id:
            entry = await Entry().get_entry(entry_id=entry_id)
        self.render("compose.html", entry=entry)

    @tornado.web.authenticated
    async def post(self):
        entry_id = self.get_argument("id", None)
        title = self.get_argument("title")
        text = self.get_argument("content-editormd-markdown-doc")
        html = self.get_argument("content-editormd-html-code")
        try:
            check_perm = bool(self.get_argument("ispublic"))
        except MissingArgumentError:
            check_perm = False
        # html = markdown.markdown(text)
        if entry_id:
            try:
                entry = await Entry().get_entry(entry_id=entry_id)
            except NoResultError:
                raise tornado.web.HTTPError(404)
            slug = entry.slug
            begin_transaction()
            await Entry().update_entry(entry_id, title, text, html, check_perm)
            commit_transaction()
        else:
            begin_transaction()
            slug = await Entry().add_entry(self.current_user, title, text, html, check_perm)
            commit_transaction()
        self.redirect("/blog/refresh/" + slug)


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
        begin_transaction()
        hashed_password = tornado.escape.to_unicode(hashed_password)
        author = await Author().add_author(self.get_argument("email"), self.get_argument("name"), hashed_password, )
        commit_transaction()
        self.set_secure_cookie("tigerblog", str(author.id))
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
            self.set_secure_cookie("tigerblog", str(author.id))
            self.render("login_ok.html", goto_url="/")
        else:
            self.render("login.html", error="incorrect password")


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("tigerblog")
        self.redirect(self.get_argument("next", "/"))


class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry, get_authorname_by_id=get_authorname_by_id)
