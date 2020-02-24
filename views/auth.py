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
from infrastructure.utils.db_conn import NoResultError
from data.author import Author
from data.entry import Entry
from data.author_operation import AuthorOperation
from business.author_process import check_password
from views.basehandler import BaseHandler


class AuthCreateHandler(BaseHandler):
    def get(self):
        self.render("create_author.html", error=None)

    async def post(self):
        try:
            author1 = await Author().get_by_email(self.get_argument("email"))
        except NoResultError:
            pass
        else:
            self.render("create_author.html", error="email已经存在，请不要重复注册！")
            return

        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(self.get_argument("password")),
            bcrypt.gensalt(),
        )
        hashed_password = tornado.escape.to_unicode(hashed_password)

        import random, string, time
        key = ''.join(random.sample(string.ascii_letters, 8))
        key = key + str(time.perf_counter())
        hash_key = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(key),
            bcrypt.gensalt(),
        )
        hash_key = tornado.escape.to_unicode(hash_key)

        author = await Author().add(self.get_argument("email"), self.get_argument("name"), hashed_password, key)

        act_link = '%s/auth/activate?author_id=%s&activate_key=%s&email=%s&create_date=%s' % \
                   (self.settings["home_domain"], author.id, hash_key, author.email, author.create_date.strftime('%Y-%m-%d %H:%M:%S'))

        mail_content = self.render_string("activate_author.html", author=author, act_link=act_link)
        import yagmail
        yag = yagmail.SMTP(user=self.settings["mail_user"], password=self.settings["mail_password"],
                           host=self.settings["mail_host"], port=self.settings["mail_port"])
        subject = "%s欢迎您" % self.settings["blog_title"]
        try:
            yag.send(to=author.email, subject=subject, contents=mail_content.decode())
        except Exception :
            await Author().delete(author.id)
            message = "无法发送激活邮件，注册失败！"
            self.render("create_author.html", error=message)
            return

        message = "欢迎注册%s，激活邮件已经发送到您的邮箱[%s]，收到邮件后点击激活链接即可激活帐户。" \
                  "提示：激活之前无法登录系统，但可以继续浏览他人写的博客。5秒钟后跳转到主页" \
                  % (self.settings["blog_title"], author.email)
        info = dict()
        info['email'] = author.email
        info['name'] = author.name
        await AuthorOperation().add(author.id, 'sign-in', self.request.headers.get("X-Real-IP", ''), str(info))
        self.render("login_ok.html", message=message, goto_url="/", delay=5000)


class AuthActivateHandler(BaseHandler):
    async def get(self):
        author_id = self.get_argument("author_id")
        key = self.get_argument("activate_key")
        create_date = self.get_argument("create_date")
        email = self.get_argument("email")
        try:
            author = Author().get(author_id)
        except NoResultError:
            self.clear_cookie("tigerwingblog")
            self.render("login_ok.html", message="帐户不存在！5秒后跳转到主页……", goto_url="/", delay=5000)
            return
        if email != author.email or author.create_date.strftime('%Y-%m-%d %H:%M:%S') != create_date:
            self.render("login_ok.html", message="email错误！5秒后跳转到主页……", goto_url="/", delay=5000)
            self.clear_cookie("tigerwingblog")
            return

        if await check_password(author.activate_key, key):
            await Author().activate_author(author_id)
            self.set_secure_cookie("tigerwingblog", author_id, expires_days=None)
            await AuthorOperation().add(author_id, 'activate', self.request.headers.get("X-Real-IP", ''))
            self.render("login_ok.html", message="email(%s)验证成功, 1秒后跳转到主页……" % email, goto_url="/", delay=1000)
        else:
            self.clear_cookie("tigerwingblog")
            self.render("login_ok.html", message="email(%s)验证失败！5秒后跳转到主页……" % email, goto_url="/", delay=5000)

class AuthLoginHandler(BaseHandler):
    async def get(self):
        self.render("login.html", error=None)

    async def post(self):
        try:
            author = await Author().get_by_email( self.get_argument("email"))
        except NoResultError:
            self.render("login.html", error="帐户不存在！")
            return
        if author.activate_state is False:
            self.render("login.html", error="帐户未激活，请到注册邮箱中点击激活链接激活帐户！")
            return
        if await check_password(self.get_argument("password"), author.hashed_password):
            await AuthorOperation().add(author.id, 'login', self.request.headers.get("X-Real-IP", ""))
            self.set_secure_cookie("tigerwingblog", str(author.id), expires_days=None)
            self.render("login_ok.html", message="登录成功，跳转到主页", goto_url="/", delay=1)
        else:
            self.render("login.html", error="密码错误！")


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("tigerwingblog")
        self.redirect(self.get_argument("next", "/"))


class AuthSettingsHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        ss = eval(self.current_user.settings)
        rr = await Entry().get_usage_by_author(self.current_user.id)
        ss['attach_usage'] = '%.2fKB' % (rr.attach_usage/1024)
        ss['usage'] = '%.2fKB' % ((rr.attach_usage+rr.txt_usage)/1024)
        self.render("settings.html", author_settings=ss, error=None)

    @tornado.web.authenticated
    async def post(self):
        default_editor = self.get_argument("default-editor")
        new_name = self.get_argument("new-name", "")

        ss = eval(self.current_user.settings)
        ss["default-editor"] = default_editor
        self.current_user.settings = str(ss)
        self.current_user.name = new_name

        await Author().update(self.current_user)
        ss['new_name'] = new_name
        await AuthorOperation().add(self.current_user.id, 'settings', self.request.headers.get("X-Real-IP", ''), str(ss))
        self.render("login_ok.html", message="设置修改成功，自动跳转到主页", goto_url="/", delay=1000)


class AuthResetHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        self.render("reset_password.html", error=None)

    @tornado.web.authenticated
    async def post(self):
        if await check_password(self.get_argument("old_password"), self.current_user.hashed_password) is not True:
            self.render("reset_password.html", error="旧密码输入错误！")
            return

        new_password = self.get_argument("password")
        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(new_password),
            bcrypt.gensalt(),
        )
        new_password = tornado.escape.to_unicode(hashed_password)
        self.current_user.hashed_password = new_password
        await Author().update(self.current_user)
        await AuthorOperation().add(self.current_user.id, 'modify_pwd', self.request.headers.get("X-Real-IP", ''))
        self.render("login_ok.html", message="密码修改成功，自动跳转到主页", goto_url="/", delay=1000)


class AuthForgetHandler(BaseHandler):
    async def get(self):
        self.render("forget_password.html", error=None)

    async def post(self):
        try:
            author = await Author().get_by_email( self.get_argument("email"))
        except NoResultError:
            self.render("forget_password.html", error="帐户不存在！")
            return

        import random, string, time
        key = ''.join(random.sample(string.ascii_letters, 8))
        key = key + str(time.perf_counter())
        hash_key = await tornado.ioloop.IOLoop.current().run_in_executor(
            None,
            bcrypt.hashpw,
            tornado.escape.utf8(key),
            bcrypt.gensalt(),
        )
        hash_key = tornado.escape.to_unicode(hash_key)

        mail_content = "<h3>尊敬的%s：</h3><br><br><p>您的密码已经重新初始化，新的密码是：%s，请务必牢记。" \
                       "</p><br><br><br><br><p>提示：请不要回复该邮件。</p>" % (author.name, key)
        import yagmail
        yag = yagmail.SMTP(user=self.settings["mail_user"], password=self.settings["mail_password"],
                           host=self.settings["mail_host"], port=self.settings["mail_port"])
        subject = "密码重置成功"
        try:
            yag.send(to=author.email, subject=subject, contents=mail_content)
        except Exception :
            message = "无法发送密码重置邮件，重置失败！"
            self.render("forget_password.html", error=message)
            return

        author.hashed_password = hash_key
        await Author().update(author)
        await AuthorOperation().add(self.current_user.id, 'forget_pwd', self.request.headers.get("X-Real-IP", ''))
        self.render("login_ok.html", message="密码重置成功，新密码已经发送到您的邮箱，请重新登录", goto_url="/", delay=2000)

