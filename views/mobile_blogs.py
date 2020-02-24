from tornado.web import RequestHandler
from tornado.escape import json_decode,json_encode
import bson
from data.entry import Entry


async def newblogs(handler: RequestHandler):
    params = json_decode(handler.request.body)

    offset = params['offset']
    fetch_size = params['fetch_size']
    offset = offset * fetch_size
    tag_key = params['tag_key']
    origin_entries, key_entries = await Entry().get_shared()
    entries = key_entries[tag_key] if len(tag_key) != 0 else origin_entries
    entry_cnt = len(entries)

    part_entries = entries[offset:offset + fetch_size]

    print('newblogs params offset[%d], fetch_size[%d], tag_key[%s]' % (offset, fetch_size, tag_key))

    result = {'success': 1, 'message': '登录成功！', 'totalCount': entry_cnt, 'entryList': part_entries}
    handler.write(bson.dumps(result))

func_normal = {
    'post_newblogs': newblogs,
}
func_authenticated = {}
