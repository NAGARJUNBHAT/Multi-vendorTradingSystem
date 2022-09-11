from hashids import Hashids
from datetime import datetime
import random 
import string 
import flask_login

def rand_id():
    k = ''.join([random.choice(string.ascii_letters 
            + string.digits) for n in range(10)]) 
    return k

class User(flask_login.UserMixin):
    pass