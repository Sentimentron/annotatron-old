from unittest import TestCase
import requests
import os.path
from models import Asset
from utils import url, authorize, remove_authorization

class TestAsset(TestCase):

    def setUp(self):
        remove_authorization()
        self.auth = authorize()
        r = requests.post(url('v1/debug/assets/remove'), auth=self.auth)
        if r.status_code != 200:
            print(r.status_code)
            print(r.text)
            assert r.status_code == 200
        self.dir = os.path.dirname(os.path.abspath(__file__))

    def test_to_json(self):
        a = Asset("test", "Example".encode("utf8"), "text/plain", "text")
        ret = a.to_json()
        self.assertEqual(ret['name'], 'test')
        self.assertEqual(ret['mime_type'], 'text/plain')
        self.assertEqual(ret['kind'], 'text')
        self.assertEqual(ret['content'], 'RXhhbXBsZQ==')

    def test_from_text_file(self):
        path = os.path.join(self.dir, "test_files", "test_1.txt")
        a = Asset.from_text_file(, path

        self.assertEqual(a.name, "test_1")
        self.assertEqual(a.content, b"This is the first test file.")
        self.assertEqual(a.mime_type, "text/plain; charset=utf8")
        self.assertEqual(a.kind, "text")

    def test_from_bytes(self):
        path = os.path.join(self.dir, "test_files", "test_1.txt")
        with open(path, 'rb') as fin:
            a = Asset.from_bytes(fin.read(), "test_1")

            self.assertEqual(a.name, "test_1")
            self.assertEqual(a.content, b"This is the first test file.")
            self.assertEqual(a.mime_type, None)
            self.assertEqual(a.kind, "text")
            self.assertEqual(a.sha_512_sum, "d90ffbc958cd4742092b5f7096fb0c0c79e2ef34ff7b3179561ac68ff82400cc63ab363e1728d76122cbeab8f645a5c1e088bcc9ab7e30a325cbaf9bf371a731")

    def test_from_json(self):
        d = {
            "name": "test",
            "mime_type": "text/plain",
            "kind": "text",
            "content": "RXhhbXBsZQ=="
        }
        a = Asset.from_json(d)
        self.assertEqual(a.name, "test")
        self.assertEqual(a.mime_type, "text/plain")
        self.assertEqual(a.kind, "text")
        self.assertEqual(a.content, b"Example")
