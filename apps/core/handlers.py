import logging
import json
from tornado.web import RequestHandler
from tornado import gen
from pycket.session import SessionMixin

import settings

logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler, SessionMixin):
    def render_string(self, template_name, **context):
        context.update({
            'xsrf': self.xsrf_form_html,
            'request': self.request,
            'user': self.current_user,
            'static': self.static_url,
            'handler': self,
            'reverse_url': self.reverse_url
        })

        return self._jinja_render(path=self.get_template_path(),
                                  filename=template_name,
                                  auto_reload=self.settings['debug'],
                                  **context)

    def _jinja_render(self, path, filename, **context):
        template = self.application.jinja_env.get_template(filename,
                                                           parent=path)
        self.write(template.render(**context))

    @property
    def is_xhr(self):
        return self.request.headers.get('X-Requested-With', '').lower() \
            == 'xmlhttprequest'

    def render_json(self, data):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))

    def get_current_user(self):
        return self.session.get('user', None)

    @property
    def db(self):
        return self.application.db

    @gen.coroutine
    def get_current_user_object(self):
        if self.current_user is not None:
            # TODO cache
            user = yield self.db[settings.AUTH_USER_COLLECTION]\
                .find_one({"_id": self.current_user})
        else:
            user = None
        self.current_user_object = user
        raise gen.Return(user)
