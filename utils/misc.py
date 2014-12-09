import hashlib
import uuid
from functools import wraps
import settings
from schematics.models import Model
import re


def make_pass(password):
    salt = uuid.uuid4().hex
    hash = hashlib.sha512(password + salt).hexdigest()
    return salt, hash


def check_pass(password, hash, salt):
    return hash == hashlib.sha512(password + salt).hexdigest()


def is_loggedin(redirect_to='index'):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwds):
            if self.session.get('user', False):
                self.redirect(self.reverse_url(redirect_to))
                return
            else:
                return method(self, *args, **kwds)
        return wrapper
    return decorator


def import_models():
    result = {}
    for app_name in settings.APPS:
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
                    result[thing().__class__.__name__] = thing
            except TypeError:
                pass

    return result
