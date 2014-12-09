from .models import UserModel
from utils.misc import make_pass


def make_password(data=None, request=None, *args, **kwargs):
    if request.arguments.get('password'):
        if getattr(data, '_id', False):
            data.set_password(request.arguments['password'][0])
            return
        data['password_salt'], data['password_hash'] = \
            make_pass(request.arguments['password'][0])
    return data


register_admin = [dict(
    name='users',
    model=UserModel,
    hidden=['pk'],
    only=None,
    exclude=['password_hash', 'password_salt'],
    extra_content='<div class="form-group">' +
                  '<label for="password">password</label>' +
                  '<input class="form-control" id="password" ' +
                  'name="password" type="password" value="">' +
                  '</div>',
    post_extra_method=make_password
)]
