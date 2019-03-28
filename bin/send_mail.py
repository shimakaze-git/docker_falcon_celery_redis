import os
import sys
import requests


sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from celery_queue.tasks import send_mail
from celery_queue.tasks import r
from celery_queue.tasks import get_mails


def request_send_mail(
    from_addr: str,
    to_addr: str,
    subject: str,
    message: str
):
    url = "http://127.0.0.1:5001"
    headers = {'content-type': 'application/json'}
    payload = {
        'fromaddr': from_addr,
        'toaddr': to_addr,
        'subject': subject,
        'msg': message
    }
    response = requests.get(
        url + "/mail",
        headers=headers,
        params=payload
    )
    return response


if __name__ == "__main__":
    # response = request_send_mail(
    #     "test@test.com",
    #     "test_send@test.com",
    #     "subject",
    #     "Message !!\n\nAdmin"
    # )
    # print(response)

    host = "localhost"
    status = send_mail(
        'test@test.com',
        'test_send@test.com',
        'subject',
        'Message !! \n\nAdmin',
        host=host
    )
