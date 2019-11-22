import tornado
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
from infrastructure.utils.db_conn import DbConnect
from tornado.options import define, options
from infrastructure.utils.common import get_size
from data.entry import one_entry_init_size


define("db_host", default="127.0.0.1", help="blog database host")
define("db_port", default=5432, help="blog database port")
define("db_database", default="blog", help="blog database name")
define("db_user", default="blog", help="blog database user")
define("db_password", default="blog", help="blog database password")
define("upload_path", default="/home/blog/tigerwingblog/static/uploads", help="uploaded files store path")

def correct_author(author_id):
    pass


def clear_delete_files(author_id):
    pass

def clear_empty_entries():
    pass

def correct_entries_statistic():
    pass

def correct_entries():
    print('Begin processing...')
    authors = DbConnect.query('select * from authors where activate_state=true and id!= 0')
    for author in authors:
        print('  Author[%s] begin process data:' % author.name)
        DbConnect.get_db_conn().begin()
        cats = DbConnect.query('select * from catalogs where author_id=0')
        for cat in cats:
            if not DbConnect.query_check('select * from entries_statistic where author_id=%s and cat_id=%s',author.id, cat.cat_id):
                DbConnect.execute('insert into entries_statistic (author_id,cat_id,parent_id,entries_cnt) values (%s,%s,%s,0)',
                                  author.id, cat.cat_id, cat.parent_id)
                print('    system catalog[%s] added to entries_statistic.' % cat.cat_name)
        cats_stats = dict()
        entries = DbConnect.query('select * from entries where author_id=%s and state = 1', 0, None, author.id)
        for entry in entries:
            if entry.cat_id in cats_stats:
                cats_stats[entry.cat_id] += 1
            else:
                cats_stats[entry.cat_id] = 1
            fpath = os.path.join(options.upload_path, str(author.id), str(entry.id))
            attach_cnt, attach_size = get_size(fpath)
            DbConnect.execute('update entries set size=%s, attach_cnt=%s, attach_size=%s where id=%s',
                              one_entry_init_size+len(entry.markdown)+len(entry.html), attach_cnt, attach_size, entry.id)
            print('    entry(%d), size(%d), attach_cnt(%d), attach_size(%d)' % (entry.id, one_entry_init_size+len(entry.markdown)+len(entry.html), attach_cnt, attach_size))
        for key in cats_stats.keys():
            DbConnect.execute('update entries_statistic set entries_cnt=%s where author_id=%s and cat_id=%s ',
                              cats_stats[key], author.id, key)
            print('    statistic author(%d), cat_id(%s), count(%d)' % (author.id, key, cats_stats[key]))
        DbConnect.get_db_conn().commit()
        print('  Author[%s] finished.' % author.name)
    print('Finished.')


def main():
    tornado.options.parse_command_line()
    DbConnect.init_db( db_host=options.db_host, db_port=options.db_port, db_user=options.db_user,
                       db_password=options.db_password, db_database=options.db_database, )
    correct_entries()


if __name__ == "__main__":
    main()

