import os
import time
import redis
import json
import ast
import requests
import random
import datetime

from celery import Celery
from celery.decorators import task

import smtplib
from email.mime.text import MIMEText


SLACK_WEBHOOK_ENDPOINT = 'https://hooks.slack.com/services/TH7GL0R4G'
SLACK_WEBHOOK_ENDPOINT += '/BHAGGNL6R/ukHVRe318gmiCuUSpVnqgm9H'

HOST = "mailhog"

pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=4
)
r = redis.StrictRedis(connection_pool=pool)


CELERY_BROKER_URL = os.environ.get(
    'CELERY_BROKER_URL', 'redis://localhost:6379'
),
CELERY_RESULT_BACKEND = os.environ.get(
    'CELERY_RESULT_BACKEND', 'redis://localhost:6379'
)

celery = Celery(
    'tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)


def get_mail_count():
    send_mail_count = r.get('send_mail_count')
    if send_mail_count is not None:
        return int(send_mail_count)
    else:
        return 0


def send_mail_count():
    send_mail_count = int(get_mail_count()) + 1
    r.set('send_mail_count', send_mail_count)


def get_mails():
    messages_list = []
    messages = r.lrange('messages', 0, -1)
    for message in messages:
        message_json = message.decode('utf8')
        # message_json = message_json.replace("'", '"')
        message_dict = ast.literal_eval(message_json)
        messages_list.append(message_dict)    
    return messages_list


def save_mail(messages):
    mes_dic = {
        'from': messages['From'],
        'to': messages['To'],
        'subject': messages['Subject'],
        'message': messages.as_string()
    }
    r.rpush('messages', mes_dic)


@celery.task(name='tasks.send_slack_message')
def send_slack_message(messages):
    attachments = []
    for i, message in enumerate(messages):
        # attachments
        attachment = {
            "author_name": "FromAddr: " + str(message['from']),
            "author_link": "",
            "author_icon": "https://s.gravatar.com/avatar/ce68aabafe314bb9524700960fe7b6dc?s=80",
            "pretext": "No. " + str(i),
            "fields": [
                {
                    "title": "Sbject: " + str(message['subject']),
                    "value": message['message']
                }
            ],
            "color": "#D00000",
            "footer": "ToAddr: " + str(message['to']),
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "ts": datetime.datetime.now().timestamp()
        }
        attachments.append(attachment)

    headers = {'content-type': 'application/json'}
    requests.post(
        SLACK_WEBHOOK_ENDPOINT,
        data=json.dumps({
            'channel': "#shimakazesoftdevelop",
            'text': "<!here> <!channel>",
            'username': 'worker_slack23',
            'icon_emoji': random.choice([
                ':ghost:', ':dog:', ':computer:', ':soccer:', ':jp:'
            ]),
            'link_names': 1,
            "attachments": attachments
        }),
        headers=headers
    )


@celery.task(name='tasks.add')
def add(x: int, y: int) -> int:
    time.sleep(5)
    return x + y


# slackへの通知処理
@task
def send_slack_notification():
    mails = get_mails()
    mails_list = []
    if len(mails) >= 5:
        for mail in mails:
            mail_dict = {
                'from': mail['from'],
                'to': mail['to'],
                'subject': mail['subject'],
                'message': mail['message']
            }
            mails_list.append(mail_dict)
        send_slack_message(mails_list)


@celery.task(name='tasks.send_mail')
def send_mail(
    fromaddr: str,
    toaddr: str,
    subject: str,
    msg: str,
    host=HOST
):
    m = MIMEText(msg)
    m['Subject'] = subject
    m['From'] = fromaddr
    m['To'] = toaddr

    s = smtplib.SMTP(host=host, port=1025)
    try:
        s.sendmail(fromaddr, toaddr, m.as_string())
        s.close()

        send_mail_count()
        save_mail(m)
        # send_slack_notification()
        send_slack_notification.delay()

        return True
    except Exception as e:
        s.close()
        return False
