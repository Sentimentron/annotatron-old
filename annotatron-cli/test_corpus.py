from unittest import TestCase
from annotatron import Annotatron
from utils import url, authorize, remove_authorization
from models import Corpus
import requests


class TestCorpus(TestCase):

    def setUp(self):
        remove_authorization()
        self.auth = authorize()
        r = requests.post(url('v1/debug/corpora/remove'), auth=self.auth)
        if r.status_code != 200:
            print(r.text)
            print(r.status_code)
            assert r.status_code == 200

    def test_to_json(self):
        corpus = Corpus("debug-sample-corpus", "An example corpus", "sample_code")
        ret = corpus.to_json()
        self.assertEqual(ret["name"], "debug-sample-corpus")
        self.assertEqual(ret["description"], "An example corpus")
        self.assertEqual(ret["question_generator"], "sample_code")

    def test_from_json(self):
        d = {
            "name": "debug-sample-corpus",
            "description": "Example",
            "question_generator": "Example"
        }
        ret = Corpus.from_json(d)
        self.assertEqual(ret.name, "debug-sample-corpus")
        self.assertEqual(ret.description, "Example")
        self.assertEqual(ret.question_generator, "Example")

    def test_upload(self):
        """
        Checks that we can upload this object to the server and retrieve it.
        """
        corpus = Corpus("debug-sample-corpus", "An example corpus", "sample_code")
        an = Annotatron(url(''), auth=self.auth)
        an.send_corpus(corpus)

        retrieved = an.get_corpus_by_name("debug-sample-corpus")
        self.assertEqual(retrieved.name, corpus.name)