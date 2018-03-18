from unittest import TestCase
from .annotatron import Annotatron, AnnotatronException
from .utils import url, authorize, remove_authorization
from .models import Corpus, Asset
import requests
import os


class TestCorpus(TestCase):

    def setUp(self):
        remove_authorization()
        self.auth = authorize()
        self.dir = os.path.dirname(os.path.abspath(__file__))
        r = requests.post(url('v1/debug/corpora/remove'), auth=self.auth)
        if r.status_code != 200:
            print(r.text)
            print(r.status_code)
            assert r.status_code == 200

    def test_to_json(self):
        corpus = Corpus("debug-sample-corpus", "An example corpus")
        ret = corpus.to_json()
        self.assertEqual(ret["name"], "debug-sample-corpus")
        self.assertEqual(ret["description"], "An example corpus")

    def test_from_json(self):
        d = {
            "name": "debug-sample-corpus",
            "description": "Example",
        }
        ret = Corpus.from_json(d)
        self.assertEqual(ret.name, "debug-sample-corpus")
        self.assertEqual(ret.description, "Example")

    def test_upload(self):
        """
        Checks that we can upload this object to the server and retrieve it.
        """
        corpus = Corpus("debug-sample-corpus", "An example corpus")
        an = Annotatron(url(''), auth=self.auth)
        an.send_corpus(corpus)

        retrieved = an.get_corpus_by_name("debug-sample-corpus")
        self.assertEqual(retrieved.name, corpus.name)

    def test_upload_bad_name(self):
        corpus = Corpus("debug-sample cor@pus", "An example corpus")
        an = Annotatron(url(''), auth=self.auth)

        with self.assertRaises(AnnotatronException):
            an.send_corpus(corpus)

    def test_upload_and_asset(self):
        """
            Checks that we can upload a corpus to the server and add some files inside.
        """

        corpus = Corpus("debug-sample-corpus", "An example corpus")
        an = Annotatron(url(''), auth=self.auth)
        an.send_corpus(corpus)

        a = Asset.from_text_file(os.path.join(self.dir, 'test_files', 'test_2.txt'), 'test_2')
        an.add_asset_to_corpus(corpus, a)

        for asset in an.list_assets_in_corpus(corpus):
            single_file = asset

        self.assertEqual(a.content, single_file.content)
