import tornado
import bcrypt


async def check_password(passwd_from_web, passwd_from_db):
    hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
        None,
        bcrypt.hashpw,
        tornado.escape.utf8(passwd_from_web),
        tornado.escape.utf8(passwd_from_db),
    )
    hashed_password = tornado.escape.to_unicode(hashed_password)
    if hashed_password == passwd_from_db:
        return True
    else:
        return False
