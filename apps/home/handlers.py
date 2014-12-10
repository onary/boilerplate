import logging
from tornado import gen
from tornado_utils.routes import route

from apps.core.handlers import BaseHandler

logger = logging.getLogger(__name__)


@route('/', name='index')
class MainHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.render('index.html')
