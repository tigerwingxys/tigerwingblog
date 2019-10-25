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



import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
from importlib import import_module
from infrastructure.utils.db_conn import DbConnect
from views import blogs, images

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("db_host", default="127.0.0.1", help="blog database host")
define("db_port", default=5432, help="blog database port")
define("db_database", default="blog", help="blog database name")
define("db_user", default="blog", help="blog database user")
define("db_password", default="blog", help="blog database password")


def include(module):
    res = import_module(module)
    urls = getattr(res, 'urls', res)
    return urls


def url_wrapper(urls):
    wrapper_list = []
    for url in urls:
        path, handles = url
        if isinstance(handles, (tuple, list)):
            for handle in handles:
                pattern, handle_class = handle
                wrap = ('{0}{1}'.format(path, pattern), handle_class)
                wrapper_list.append(wrap)
        else:
            wrapper_list.append((path, handles))
    return wrapper_list


class Application(tornado.web.Application):
    def __init__(self):

        settings = dict(
            blog_title=u"虎翼博客",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Entry": blogs.EntryModule},
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=True,
        )
        handlers = [
            (r"/", blogs.HomeHandler),
            (r"/blog/myblogs(\d+)-(\d+)", blogs.MyBlogHandler),
            (r"/blog/myblogtree", blogs.MyBlogTreeHandler),
            (r"/blog/entry/([^/]+)", blogs.blogEntryHandler),
            (r"/blog/refresh/([^/]+)", blogs.blogRefreshEntryHandler),
            (r"/blog/archive(\d+)-(\d+)", blogs.ArchiveHandler),
            (r"/blog/search(\d+)-(\d+)/(.+)", blogs.SearchHandler),
            (r"/blog/compose", blogs.ComposeHandler),
            (r"/share/entry/([^/]+)", blogs.ShareEntryHandler),
            (r"/feed", blogs.FeedHandler),
            (r"/images/upload", images.UploadHandler, dict(upload_path=os.path.join(settings["static_path"], "uploads"), naming_strategy=None)),
            (r"/images/image(.*)", images.DownloadHandler, dict(base_path=os.path.join(settings["static_path"], "uploads"))),
            (r"/auth/create", blogs.AuthCreateHandler),
            (r"/auth/login", blogs.AuthLoginHandler),
            (r"/auth/logout", blogs.AuthLogoutHandler),
        ]

        super(Application, self).__init__(handlers, **settings)




async def main():
    tornado.options.parse_command_line()

    DbConnect.init_db( db_host=options.db_host, db_port=options.db_port, db_user=options.db_user,
                    db_password=options.db_password, db_database=options.db_database, )

    app = Application()
    app.listen(options.port)

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
