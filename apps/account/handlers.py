import logging
import tornado.web
import tornado.escape
from tornado import gen
from tornado.auth import FacebookGraphMixin
from tornado_utils.routes import route
from pymongo.errors import DuplicateKeyError

from utils.misc import is_loggedin
from apps.core.handlers import BaseHandler, AuthMixin
from .forms import RegistrationForm, LoginForm
from .models import UserModel

logger = logging.getLogger(__name__)


@route('/login', name='login')
class LoginHandler(BaseHandler, AuthMixin):

    @is_loggedin(redirect_to='index')
    def get(self):
        self.render('account/login.html', form=LoginForm())

    @gen.coroutine
    @is_loggedin(redirect_to='index')
    def post(self):
        form = LoginForm(self.request.arguments)
        if form.validate():
            user = yield UserModel.find_one(self.db, {
                "email": form.email.data})
            if user:
                if user.check_password(form.password.data):
                    self.set_session(str(user.email or user._id))
                    self.redirect(self.reverse_url('index'))
                    return
                else:
                    form.set_field_error('password', 'wrong_password')
            else:
                form.set_field_error('email', 'not_found')
        self.render('account/login.html', form=form)


@route('/', name='index')
class MainHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.render('index.html')


@route('/facebook_login', name='fb_login')
class FacebookLoginHandler(BaseHandler, FacebookGraphMixin, AuthMixin):
    @tornado.gen.coroutine
    @is_loggedin(redirect_to='index')
    def get(self):
        if self.get_argument('code', False):
            fb_user = yield self.get_authenticated_user(
                redirect_uri=self.settings['fb_redirect_url'],
                client_id=self.application.settings['fb_app_id'],
                client_secret=self.application.settings['fb_secret'],
                code=self.get_argument('code'))

            user = yield UserModel.find_one(self.db,
                                            {'provider_id': fb_user['id']})

            if user is None:
                user = UserModel({
                    'first_name': fb_user.get('first_name', ''),
                    'last_name': fb_user.get('last_name', ''),
                    'email': fb_user.get('email', ''),
                    'photo': fb_user['picture']['data']['url'],
                    'provider': 'facebook',
                    'provider_id': fb_user.get('id', '')
                })

                yield user.insert(self.db)

            self.set_session(str(user.email or user._id))
            self.redirect(self.reverse_url('index'))
        else:
            yield self.authorize_redirect(
                redirect_uri=self.settings['fb_redirect_url'],
                client_id=self.settings['fb_app_id'],
                extra_params={'scope': 'offline_access'})


@route('/logout', name='logout')
class LogoutHandler(BaseHandler):
    def get(self):
        self.session.delete('user')
        self.redirect(self.reverse_url('index'))


@route('/signup', name='signup')
class RegisterHandler(AuthMixin, BaseHandler):
    @is_loggedin(redirect_to='index')
    def get(self):
        self.render('account/signup.html', form=RegistrationForm())

    @tornado.gen.coroutine
    @is_loggedin(redirect_to='index')
    def post(self):
        form = RegistrationForm(self.request.arguments)
        if form.validate():
            user = form.get_object()
            user.set_password(user.password)
            try:
                yield user.insert(self.db)
                # print user
            except DuplicateKeyError:
                form.set_field_error('email', 'email_occupied')
            else:
                # user save succeeded
                self.set_session(str(user.email or user._id))
                self.redirect(self.reverse_url('index'))
                return
        self.render('account/signup.html', form=form)
