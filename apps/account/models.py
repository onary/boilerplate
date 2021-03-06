import datetime
from schematics.types import StringType, EmailType, DateTimeType, \
    BooleanType
from apps.core.models import BaseModel
from utils.misc import check_pass, make_pass


class UserModel(BaseModel):
    first_name = StringType(default='')
    last_name = StringType(default='')
    email = EmailType(required=True)
    photo = StringType(default='')
    provider = StringType(default='')
    provider_id = StringType(default='')
    password_hash = StringType(default='')
    password_salt = StringType(default='')
    created_at = DateTimeType(default=datetime.datetime.now)
    superuser = BooleanType(default=False)

    verbose_name = "User"
    verbose_name_plural = "Users"

    MONGO_COLLECTION = 'accounts'
    NEED_SYNC = True
    INDEXES = ({'name': 'email', 'unique': True}, {'name': 'provider'},)

    def check_password(self, password):
        return check_pass(password, self.password_hash, self.password_salt)

    def set_password(self, password):
        self.password_salt, self.password_hash = make_pass(password)

    def __unicode__(self):
        return "User %s" % (self.email or self._id)
