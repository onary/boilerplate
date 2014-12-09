import logging
import json
from tornado.web import RequestHandler
from tornado import gen
import tornado.escape
from pycket.session import SessionMixin

import settings

from schematics_wtf.converter import model_form
from apps.core.forms import ModelForm
from bson.objectid import ObjectId
from apps.core.forms import AdminLoginForm
from tornado_utils.routes import route
from utils.misc import is_loggedin
from utils.admin import authenticated

logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler, SessionMixin):
    def render_string(self, template_name, **context):
        context.update({
            'xsrf': self.xsrf_form_html,
            'request': self.request,
            'user': self.current_user,
            'static': self.static_url,
            'handler': self,
            'reverse_url': self.reverse_url,

            'assets': self.application.assets,
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


class AuthMixin(object):
    def set_current_user(self, user):
        if user:
            self.set_secure_cookie('user', tornado.escape.json_encode(user))
        else:
            self.clear_cookie('user')

    def set_session(self, user):
        if user:
            self.session.set('user', user)


@route(r"/admin-login", name='admin_login')
class AdminLoginHandler(AuthMixin, BaseHandler):
    @is_loggedin(redirect_to='admin_main')
    def get(self):
        self.render('admin/login.html', form=AdminLoginForm())

    @gen.coroutine
    @is_loggedin(redirect_to='admin_main')
    def post(self):
        form = AdminLoginForm(self.request.arguments)
        model = self.application.models.get(settings.AUTH_USER_MODEL, False)
        # TODO: 404 page
        if not model:
            pass
        if form.validate():
            user = yield model.find_one(self.db, {
                "email": form.email.data})
            if user and user.superuser:
                if user.check_password(form.password.data):
                    self.set_session(str(user.email or user._id))
                    self.session.set('superuser', str(user._id))
                    self.redirect(self.reverse_url('admin_main'))
                    return
                else:
                    form.set_field_error('password', 'wrong_password')
            else:
                form.set_field_error('email', 'not_found')
        self.render('admin/login.html', form=form)


# @route(r"/admin", name='admin_main')
# @route(r'/admin/(.+)', name='admin_list')
# @route(r'/admin/(.+)/(.+)', name='admin_modify')
# class AdminHandler(AuthMixin, BaseHandler):
#     @authenticated()
#     def get(self, slug=None, id=None):
#         if not slug:
#             self.render('admin/main.html', obj=self.application.admin_apps)
#         else:
#             pass

@route(r'/admin', name='admin_main')
class AdminMainHandler(AuthMixin, BaseHandler):
    @authenticated()
    def get(self):
        self.render('admin/main.html', obj=self.application.admin_apps)


@route(r'/admin/list/(.+)', name='admin_list')
class AdminListHandler(AuthMixin, BaseHandler):
    @gen.coroutine
    @authenticated()
    def get(self, slug):
        item = self.application.admin_apps.get(slug, {})
        model = item.get('model', None)
        response = dict(
            item=item,
            model=model,
            slug=slug)
        if model:
            cursor = model.get_cursor(self.db, {})
            response['query'] = yield model.find(cursor)
        self.render('admin/list.html', **response)


@route(r'/admin/edit/(.+)/(.+)', name='admin_edit')
class AdminEditHandler(AuthMixin, BaseHandler):
    @gen.coroutine
    @authenticated()
    def get(self, slug, id):
        item = self.application.admin_apps.get(slug, {})
        model = item.get('model', None)
        response = dict(
            item=item,
            model=model,
            slug=slug,
            extra=item.get('extra_content', None))
        if model:
            obj = yield model.find_one(self.db, {"_id": ObjectId(id)})
            response['form'] = \
                model_form(model, base_class=ModelForm,
                           only=item.get('only', None),
                           exclude=item.get('exclude', None),
                           hidden=item.get('hidden', [])
                           )(**obj)
        self.render('admin/edit.html', **response)

    @gen.coroutine
    @authenticated()
    def post(self, slug, id):
        item = self.application.admin_apps.get(slug, {})
        model = item.get('model', None)
        response = dict(
            item=item,
            model=model,
            slug=slug,
            extra=item.get('extra_content', None))
        if model:
            form = model_form(model, base_class=ModelForm,
                              only=item.get('only', None),
                              exclude=item.get('exclude', None),
                              hidden=item.get('hidden', [])
                              )(self.request.arguments)

            if form.validate():
                obj = yield model.find_one(self.db, {"_id": ObjectId(id)})
                data = form.data
                if item.get('post_extra_method', None):
                    data = item['post_extra_method'](data, self.request)
                try:
                    yield obj.update(self.db, update=data)
                    response['success'] = True
                except Exception, e:
                    raise e
            response['form'] = form
        self.render('admin/edit.html', **response)


@route(r'/admin/new/(.+)', name='admin_new')
class AdminNewHandler(AuthMixin, BaseHandler):
    @authenticated()
    def get(self, slug):
        item = self.application.admin_apps.get(slug, {})
        model = item.get('model', None)
        response = dict(
            item=item,
            model=model,
            slug=slug,
            extra=item.get('extra_content', None))
        if model:
            response['form'] = \
                model_form(model, base_class=ModelForm,
                           only=item.get('only', None),
                           exclude=item.get('exclude', None),
                           hidden=item.get('hidden', [])
                           )()
        self.render('admin/new.html', **response)

    @gen.coroutine
    @authenticated()
    def post(self, slug):
        item = self.application.admin_apps.get(slug, {})
        model = item.get('model', None)
        response = dict(
            item=item,
            model=model,
            slug=slug,
            extra=item.get('extra_content', None))
        if model:
            form = model_form(model, base_class=ModelForm,
                              only=item.get('only', None),
                              exclude=item.get('exclude', None),
                              hidden=item.get('hidden', [])
                              )(self.request.arguments)

            if form.validate():
                obj = form.get_object()
                if item.get('post_extra_method', None):
                    item['post_extra_method'](obj, self.request)
                try:
                    yield obj.insert(self.db)
                    response['success'] = True
                except Exception, e:
                    raise e
            response['form'] = form
        self.render('admin/new.html', **response)


@route(r'/admin/show/(.+)/(.+)', name='admin_show')
class AdminShowHandler(AuthMixin, BaseHandler):
    @gen.coroutine
    @authenticated()
    def get(self, slug, id):
        item = self.application.admin_apps.get(slug, {})
        model = item.get('model', None)
        response = dict(
            item=item,
            model=model,
            slug=slug)
        if model:
            response['query'] = \
                yield model.find_one(self.db, {"_id": ObjectId(id)})
        self.render('admin/show.html', **response)


@route(r'/admin/delete/(.+)/(.+)', name='admin_delete')
class AdminDeleteHandler(AuthMixin, BaseHandler):
    @gen.coroutine
    @authenticated()
    def delete(self, slug, id):
        if self.is_xhr:
            item = self.application.admin_apps.get(slug, {})
            model = item.get('model', None)
            try:
                obj = yield model.find_one(self.db, {"_id": ObjectId(id)})
                yield obj.remove(self.db)
            except Exception, e:
                raise e
            self.write(self.reverse_url('admin_list', slug))
            self.finish()
            return
        self.redirect(self.reverse_url('admin_list', slug))
