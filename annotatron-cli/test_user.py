from unittest import TestCase

import requests
from requests.auth import HTTPBasicAuth

from pyannotatron import User, ConfigurationResponse
from utils import url


class TestUser(TestCase):

    def setUp(self):
        r = requests.post(url('v1/debug/users/remove'))
        print(r.status_code)
        print(r.text)
        assert r.status_code == 200

    def test_user_from_json(self):
        json = {
            "username": "richard.townsend",
            "email": "someone@somewhere.org",
            "password": "Humpty",
            "is_superuser": True,
            "is_staff": True
        }

        user = User.from_json(json)
        self.assertEqual(user.super_user, True)
        self.assertEqual(user.staff_user, True)
        self.assertEqual(user.password, "Humpty")
        self.assertEqual(user.username, "richard.townsend")
        self.assertEqual(user.email, "someone@somewhere.org")

    def test_user_to_json(self):
        u = User("richard.townsend", "humpty", "someone@somewhere.com", False, True)
        json = u.to_json()
        self.assertEqual(json['is_superuser'], False)
        self.assertEqual(json['is_staff'], True)
        self.assertEqual(json['password'], 'humpty')
        self.assertEqual(json['email'], 'someone@somewhere.com')
        self.assertEqual(json['username'], 'richard.townsend')

    def test_debug_create(self):
        u = User("debug-user", "debug", "debug@debug.com", True, True)
        r = requests.post(url('v1/debug/users/'), json=u.to_json())
        self.assertEqual(r.status_code, 201)

        r = requests.post(url('v1/debug/hello'), auth=HTTPBasicAuth('debug-user', 'debug'))

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["hello"], "world")

        r = requests.get(url('v1/control/setup'))
        response = ConfigurationResponse.from_json(r.json())
        self.assertFalse(response.requires_setup)

    def test_initial_configuration(self):
        u = User("debug-user", "debug", "debug@debug.com", True, True)
        r = requests.post(url('v1/debug/users/'), json=u.to_json())
        self.assertEqual(r.status_code, 201)

        r = requests.post(url('v1/debug/hello'), auth=HTTPBasicAuth('debug-user', 'debug'))
        self.assertEqual(r.status_code, 200)

        r = requests.post(url("v1/control/setup"), json=u.to_json())
        self.assertEqual(r.status_code, 401)

