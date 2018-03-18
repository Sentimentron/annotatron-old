from unittest import TestCase
import requests
import os.path
from pyannotatron import Corpus, Annotatron, Asset, Annotation
from utils import url, authorize, remove_authorization


class TestAnnotation(TestCase):

    def setUp(self):
        remove_authorization()
        self.auth = authorize()
        r = requests.post(url('v1/debug/corpora/remove'), auth=self.auth)
        if r.status_code != 200:
            print(r.text)
            print(r.status_code)
            assert r.status_code == 200
        r = requests.post(url('v1/debug/assets/remove'), auth=self.auth)
        if r.status_code != 200:
            print(r.status_code)
            print(r.text)
            assert r.status_code == 200
        self.dir = os.path.dirname(os.path.abspath(__file__))

        # Create a starting Corpus and Asset to upload onto
        self.corpus = Corpus("debug-sample-corpus", "An example corpus")
        self.an = Annotatron(url(''), auth=self.auth)
        self.an.send_corpus(self.corpus)

        self.a = Asset.from_text_file(os.path.join(self.dir, 'test_files', 'test_2.txt'), 'test_2')
        self.an.add_asset_to_corpus(self.corpus, self.a)

    def test_to_json(self):
        """
        :return: s
        """
        a = Annotation("TRANSCRIPT", "This is an example", "text", "user")
        ret = a.to_json()
        self.assertEqual(ret["summary_code"], "TRANSCRIPT")
        self.assertEqual(ret["data"], "This is an example")
        self.assertEqual(ret["kind"], "text")
        self.assertEqual(ret["source"], "user")

    def test_from_json(self):
        data = {
            "summary_code": "WORDS",
            "data": [1.0, 2.0],
            "kind": "1d_segmentation",
            "source": "user",
            "metadata": {}
        }
        an = Annotation.from_json(data)
        self.assertEqual(an.summary_code, "WORDS")
        self.assertAlmostEqual(an.data[0], 1.0)
        self.assertAlmostEqual(an.data[1], 2.0)
        self.assertEqual(len(an.data), 2)
        self.assertEqual(an.kind, "1d_segmentation")
        self.assertEqual(an.source, "user")

    def test_upload_reference(self):
        a = Annotation("TRANSCRIPT", "This is an example", "text", "reference")
        b = self.an.add_annotation_to_asset(self.corpus, self.a, a)
        self.assertEqual(a, b)

        entries = self.an.retrieve_asset_annotations(self.corpus, self.a)
        self.assertTrue("reference" in entries)
        self.assertEqual(len(entries), 1)

        reference_annotations = entries["reference"]
        self.assertTrue("TRANSCRIPT" in reference_annotations)
        self.assertEqual(len(reference_annotations), 1)

        annotations = reference_annotations["TRANSCRIPT"]
        self.assertEqual(len(annotations), 1)

        annotation = annotations[0]
        self.assertEqual(annotation.data, "This is an example")

    def test_upload_system(self):
        a = Annotation("TRANSCRIPT", "This is an example", "text", "system")
        b = self.an.add_annotation_to_asset(self.a, a)
        self.assertEqual(a, b)

        entries = self.an.retrieve_asset_annotations(self.corpus, self.a)
        self.assertTrue("system" in entries)
        self.assertEqual(len(entries), 1)

        reference_annotations = entries["reference"]
        self.assertTrue("TRANSCRIPT" in reference_annotations)
        self.assertEqual(len(reference_annotations), 1)

        annotations = reference_annotations["TRANSCRIPT"]
        self.assertEqual(len(annotations), 1)

        annotation = annotations[0]
        self.assertEqual(annotation.data, "This is an example")

