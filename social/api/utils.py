import string
import secrets
import random
import re

#from ..models import ActivationCode, SMSToken
from .tasks import send_activation_code


class Str:
    @staticmethod
    def randStr(len=64):
        alphabet = string.ascii_letters + string.digits
        while True:
            randStr = ''.join(secrets.choice(alphabet) for i in range(len))
            if (any(c.islower() for c in randStr)
                    and any(c.isupper() for c in randStr)
                    and sum(c.isdigit() for c in randStr) >= 9):
                break

        return randStr

    @staticmethod
    def rand_num(min_num=1100, max_num=9999991):
        return random.randint(min_num, max_num)


