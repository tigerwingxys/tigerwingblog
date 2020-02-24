from tornado.util import ObjectDict
from tornado.escape import json_encode,json_decode
from tornado.web import RequestHandler
import views.mobile_auth
import views.mobile_blogs

class CommandError(Exception):
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    @staticmethod # known case of __new__
    def __new__(*args, **kwargs): # real signature unknown
        pass


proc_normal = ObjectDict()
proc_normal.update(views.mobile_auth.func_normal)
proc_normal.update(views.mobile_blogs.func_normal)
proc_authenticated = ObjectDict()
proc_authenticated.update(views.mobile_auth.func_authenticated)
proc_authenticated.update(views.mobile_blogs.func_authenticated)



async def process(handler: RequestHandler, method: str, func_dict: ObjectDict):
    command = handler.get_argument('command', None)
    if command is None:
        result = {'success': 0, 'message': 'command is not given.'}
        handler.write(json_encode(result))

    func = func_dict[method + '_' + command]
    if func is None:
        raise CommandError('command[%s][%s] is not defined.' % (command, method))
    await func(handler)


async def process_normal(handler: RequestHandler, method: str):
    await process(handler, method, proc_normal)


async def process_authenticated(handler: RequestHandler, method: str):
    await process(handler, method, proc_authenticated)
