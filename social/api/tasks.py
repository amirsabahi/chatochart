from .celery import app, get_token
from celery.schedules import crontab
from django.core.mail import send_mail
import requests
import json



@app.task
def send_activation_code(mobile, code, token):
    data = {
        "ParameterArray": [
            {"Parameter": "VerificationCode", "ParameterValue": code},
        ],
        "Mobile": mobile,
        "TemplateId": "64855"}

    # Make a request
    try:
        headers = {"Content-Type": "application/json", "x-sms-ir-secure-token": token}
        req = requests.post(url='https://RestfulSms.com/api/UltraFastSend',
                            data=json.dumps(data),
                            headers=headers, verify=False,)

        if req.status_code == 201:
            r = req.json()
            if not r['IsSuccessful']:
                get_token('')

    except requests.exceptions.JSONDecodeError:
        print('JSONDecodeError')
        pass
    except requests.exceptions.RequestException:
        print('RequestException')
        pass
    except requests.exceptions.ConnectionError:
        print('ConnectionError')
        pass
    except requests.exceptions.ConnectTimeout:
        print('ConnectTimeout')
        pass
    except Exception:
        print('Exception')
        pass
    print('End')

def send_invitation(code):
    pass







