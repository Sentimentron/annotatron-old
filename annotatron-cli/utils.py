import os
import requests
from requests.auth import HTTPBasicAuth

from models import User


def url(path):
    base_path = os.getenv("AN_URL")
    if base_path is None:
        base_path = "http://localhost/annotatron/"
    return base_path + path


def authorize():
    """
    Creates and returns an authorization for a debug, admin user.
    :return: HTTPBasicAuth, ready for use with requests.
    """
    u = User("debug-user", "debug", "debug@debug.com", True, True)
    r = requests.post(url('v1/debug/users/'), json=u.to_json())
    if r.status_code != 201:
        print(r.text)
        assert r.status_code == 201

    r = requests.post(url('v1/debug/hello'), auth=HTTPBasicAuth('debug-user', 'debug'))
    assert r.status_code == 200

    return HTTPBasicAuth('debug-user', 'debug')

def remove_authorization():
    """
    Removes all temporary debug users.
    :return:
    """
    r = requests.post(url('v1/debug/users/remove'))
    assert r.status_code == 200
