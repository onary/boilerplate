import settings
from functools import wraps


def get_admin_apps():
    admin_apps = {}
    for app_name in settings.APPS:
        admin_list = []
        try:
            admin_list = __import__('apps.%s.admin' % app_name,
                                    globals(),
                                    locals(),
                                    ['admin'], 0).register_admin
        except ImportError:
            continue
        except AttributeError:
            continue
        for a in admin_list:
            a['app'] = app_name
            admin_apps[a.pop("name", 'Undefined')] = a

    return admin_apps


def authenticated(redirect_to='admin_login'):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwds):
            if not self.session.get('superuser', False):
                self.redirect(self.reverse_url(redirect_to))
                return
            else:
                return method(self, *args, **kwds)
        return wrapper
    return decorator
