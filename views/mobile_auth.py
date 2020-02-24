from tornado.web import RequestHandler
from tornado.escape import json_decode,json_encode
import bson
import base64
from data.author import Author
from data.author_operation import AuthorOperation
from infrastructure.utils.db_conn import NoResultError
from business.author_process import check_password


async def get_token(handler: RequestHandler):
    result = {'success': 1, 'message': 'ok', 'token': str(handler.xsrf_token, encoding='utf-8')}
    handler.write(bson.dumps(result))


async def login(handler: RequestHandler):
    params = json_decode(handler.request.body)
    usercode = str(base64.b64decode(params['login_data']), encoding='utf-8')
    idx = usercode.index(':')
    email = usercode[:idx]
    passwd = usercode[idx+1:]
    try:
        author = await Author().get_by_email(email)
    except NoResultError:
        result = {'success': 0, 'message': '账户不存在！'}
        handler.write(bson.dumps(result))
        return
    if author.activate_state is False:
        result = {'success': 0, 'message': '账户未激活，请到注册邮箱中点击激活链接激活帐户！'}
        handler.write(bson.dumps(result))
        return
    if await check_password(passwd, author.hashed_password):
        await AuthorOperation().add(author.id, 'login', handler.request.headers.get("X-Real-IP", ""))
        handler.set_secure_cookie("tigerwingblog", str(author.id))
        result = {'success': 1, 'message': '登录成功！', 'author': author}
        handler.write(bson.dumps(result))
    else:
        result = {'success': 0, 'message': '密码错误！'}
        handler.write(bson.dumps(result))

func_normal = {
    'get_token': get_token,
    'post_login': login,
}
func_authenticated = {}
