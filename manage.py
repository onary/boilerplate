import sys
import tornado
import tornado.web
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from tornado_utils.routes import route

import settings
from utils import filters
from utils.db import connect_mongo, create_superuser
from utils.admin import get_admin_apps
from utils.misc import import_models


define("port", default=8888, type=int)
define("autoreload", default=False, type=bool)

for app_name in settings.APPS:
    # import all handlers so their routes are registered
    __import__('apps.%s' % app_name, globals(), locals(), ['handlers'], -1)


class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        # Init jiaja2 environment
        self.jinja_env = settings.JINJA_ENV
        # Register filters for jinja2
        self.jinja_env.filters.update(filters.register_filters())
        self.jinja_env.tests.update({})
        self.jinja_env.globals['settings'] = settings.APP_SETTINGS
        handlers = route.get_routes()

        # Register mongo db
        self.db = connect_mongo(settings.MONGO_DB, **kwargs)

        # compress css and js
        self.assets = lambda x: settings.ASSETS[x].urls()[0]

        # registr admin list
        self.admin_apps = get_admin_apps()

        # registr models
        self.models = import_models()

        tornado.web.Application.__init__(
            self, handlers, *args, **dict(settings.APP_SETTINGS, **kwargs))


def runserver():
    tornado.options.parse_command_line()
    http_server = HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    loop = tornado.ioloop.IOLoop.instance()
    print 'Server running on http://localhost:%d' % (options.port)
    loop.start()


def syncdb():
    from pymongo import MongoClient
    db = MongoClient(host=settings.MONGO_DB['host'],
                     port=settings.MONGO_DB['port']
                     )[settings.MONGO_DB['db_name']]

    models = import_models()
    for k, model in models.items():
        if hasattr(model, 'NEED_SYNC'):
            collection = model.MONGO_COLLECTION
            # db.drop_collection(collection)
            for index in model.INDEXES:
                i_name = index.pop('name')
                db[collection].create_index(i_name, **index)
            if settings.AUTH_USER_COLLECTION == collection:
                su = raw_input("Superuser doesn't exist. Do you"
                               " want to create it? (y/n)\n")
                if str(su) == "y":
                    create_superuser(db[collection])


def createsuperuser():
    from pymongo import MongoClient
    db = MongoClient(host=settings.MONGO_DB['host'],
                     port=settings.MONGO_DB['port']
                     )[settings.MONGO_DB['db_name']]
    collection = settings.AUTH_USER_COLLECTION
    create_superuser(db[collection])


if __name__ == '__main__':
    if 'runserver' in sys.argv:
        runserver()
    elif 'syncdb' in sys.argv:
        syncdb()
    elif 'createsuperuser' in sys.argv:
        createsuperuser()
