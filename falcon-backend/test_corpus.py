from falcon import testing
import falcon

from pyannotatron.models import Corpus

from test_users import TestCaseWithEachUserType

class TestCorpusResources(TestCaseWithEachUserType):

    def test_initially_empty(self):
        response = self.simulate_get("/corpus")
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.assertEqual(response.json, [])

    def test_can_create(self):
        c = Corpus("test_corpus", "Some really long MarkDown description", copyright="Copyright (c) 2010 some guy")
        response = self.simulate_post("/corpus", json=c.to_json())
        self.assertEqual(response.status, falcon.HTTP_201)

        response = self.simulate_get("/corpus")
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.assertEqual(response.json, ["test_corpus"])

        response = self.simulate_get("/corpus/test_corpus")
        self.assertEqual(response.status, falcon.HTTP_OK)

        ret = Corpus.from_json(response.json)

        self.assertEqual(ret.name, c.name)
        self.assertEqual(ret.description, c.description)
        self.assertEqual(ret.copyright, c.copyright)
