import sys
import re
import tornado
import tornado.web
from tornado.httpserver import HTTPServer
from tornado.options import define, options

from lib import filters
from lib.db import connect_mongo, create_superuser
from settings import APP_SETTINGS, JINJA_ENV, MONGO_DB, APPS, \
    AUTH_USER_COLLECTION
# from urls import handlers
from tornado_utils.routes import route


define("port", default=8888, type=int)
define("autoreload", default=False, type=bool)


class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        # Init jiaja2 environment
        self.jinja_env = JINJA_ENV
        # Register filters for jinja2
        self.jinja_env.filters.update(filters.register_filters())
        self.jinja_env.tests.update({})
        self.jinja_env.globals['settings'] = APP_SETTINGS
        handlers = route.get_routes()

        tornado.web.Application.__init__(
            self, handlers, *args, **dict(APP_SETTINGS, **kwargs))

        # Register mongo db
        self.db = connect_mongo(MONGO_DB, **kwargs)


for app_name in APPS:
    # import all handlers so their routes are registered
    __import__('apps.%s' % app_name, globals(), locals(), ['handlers'], -1)


def runserver():
    tornado.options.parse_command_line()
    http_server = HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    loop = tornado.ioloop.IOLoop.instance()
    print 'Server running on http://localhost:%d' % (options.port)
    loop.start()


def syncdb():
    from schematics.models import Model
    from pymongo import MongoClient
    db = MongoClient(host=MONGO_DB['host'],
                     port=MONGO_DB['port'])[MONGO_DB['db_name']]
    for app_name in APPS:
        _models = __import__('apps.%s' % app_name, globals(), locals(),
                             ['models'], -1)
        try:
            models = _models.models
        except AttributeError:
            # this app simply doesn't have a models.py file
            continue

        for name in [x for x in dir(models) if re.findall('[A-Z]\w+', x)]:
            thing = getattr(models, name)

            try:
                if issubclass(thing, Model):
                    if hasattr(thing, 'NEED_SYNC'):
                        collection = thing.MONGO_COLLECTION
                        db.drop_collection(collection)
                        for index in thing.INDEXES:
                            i_name = index.pop('name')
                            db[collection].create_index(i_name, **index)
                        if AUTH_USER_COLLECTION == collection:
                            su = raw_input("Superuser doesn't exist. Do you"
                                           " want to create it? (y/n)\n")
                            if str(su) == "y":
                                create_superuser(db[collection])
            except TypeError:
                pass


def createsuperuser():
    from pymongo import MongoClient
    db = MongoClient(host=MONGO_DB['host'],
                     port=MONGO_DB['port'])[MONGO_DB['db_name']]
    collection = AUTH_USER_COLLECTION
    create_superuser(db[collection])


if __name__ == '__main__':
    if 'runserver' in sys.argv:
        runserver()
    elif 'syncdb' in sys.argv:
        syncdb()
    elif 'createsuperuser' in sys.argv:
        createsuperuser()
