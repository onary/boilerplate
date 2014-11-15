import motor
import time
import logging
from pymongo.errors import ConnectionFailure
from utils.misc import make_pass

l = logging.getLogger(__name__)


def connect_mongo(mongo_settings, **kwargs):
    mongo_addr = kwargs.get('mongo_addr', {'host': mongo_settings['host'],
                                           'port': mongo_settings['port']})
    mongo_db = kwargs.get('mongo_db', mongo_settings['db_name'])
    db = None
    for i in xrange(mongo_settings['reconnect_tries'] + 1):
        try:
            db = motor.MotorClient(**mongo_addr)[mongo_db]
        except ConnectionFailure:
            if i >= mongo_settings['reconnect_tries']:
                raise
            else:
                timeout = mongo_settings['reconnect_timeout']
                l.warning("ConnectionFailure #{0} during server start, "
                          "waiting {1} seconds".format(i + 1, timeout))
                time.sleep(timeout)
        else:
            break
    return db


def create_superuser(collection):
    email = str(raw_input("Enter email:  "))
    password = str(raw_input("Enter password:  "))
    salt, hash = make_pass(password)
    try:
        collection.save(dict(email=email, password_hash=hash,
                             password_salt=salt, superuser=True))
    except Exception, e:
        raise e
