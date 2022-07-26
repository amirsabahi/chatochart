import os
from celery import Celery
from django.apps import apps
import requests
from django.conf import settings


# set the default Django settings module for the 'celery' program.
'''
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'watchbist.settings')
app = Celery('watchbist', broker='pyamqp://guest@localhost//')
app.config_from_object('django.conf:settings', namespace='CELERY')
'''


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'watchbist_social.settings')
RABBITQM_URI = settings.RABBITQM_URI
app = Celery('social', broker=RABBITQM_URI)
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(1500.0, get_token.s(''), name='add every 1', expires=30)


@app.task
def get_token(arg):
    # Make a request
    try:
        req = requests.post(url='https://RestfulSms.com/api/Token', data={'UserApiKey': '3032a0405a475ea4f0968ee5',
                                                                          'SecretKey': 'HS2##93847#heLPY9f0@8ST0493utr0e!9ytf'}
                            , json=True,)

        if req.status_code == 201:
            replay = req.json()

            from ..models import SMSToken

            SMSToken.objects.update_or_create(id=1, defaults={'token': replay['TokenKey'], 'is_refreshed': True})
    except requests.exceptions.JSONDecodeError:
        SMSToken.objects.update_or_create(id=1, defaults={'token': '', 'is_refreshed': False})
    except requests.exceptions.RequestException:
        SMSToken.objects.update_or_create(id=1, defaults={'token': '', 'is_refreshed':False})
    except requests.exceptions.ConnectionError:
        SMSToken.objects.update_or_create(id=1, defaults={'token': '', 'is_refreshed':False})
    except requests.exceptions.ConnectTimeout:
        SMSToken.objects.update_or_create(id=1, defaults={'token': '', 'is_refreshed':False})
    except Exception:
        SMSToken.objects.update_or_create(id=1, defaults={'token': '', 'is_refreshed':False})
