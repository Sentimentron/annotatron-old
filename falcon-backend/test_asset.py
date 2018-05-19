from falcon import testing
import falcon
import hashlib

from pyannotatron.models import Corpus, BinaryAsset, BinaryAssetKind

from test_corpus import TestCaseWithDefaultCorpus

class TestAssetLifecycleBase(TestCaseWithDefaultCorpus):

    def create_default_asset(self):
        m = hashlib.sha512()
        m.update("ハロー・ワールド".encode("utf8"))
        m = m.hexdigest()

        b = BinaryAsset(content="ハロー・ワールド".encode("utf8"), metadata={"someKey": {"someChildKey": "someValue"}},
                        copyright="No redistribution", mime_type="text/plain",
                        type_description=BinaryAssetKind.UTF8_TEXT,
                        checksum=m)

        response = self.simulate_post("/corpus/test_corpus/assets/testFile", json=b.to_json())
        self.assertEqual(response.status, falcon.HTTP_201)


class TestAssetLifecycleUpload(TestAssetLifecycleBase):
    def test_asset_upload(self):
        self.create_default_asset()

    def test_corpus_initially_empty(self):
        response = self.simulate_get("/corpus/test_corpus/assets")
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.assertEqual(response.json, [])


class TestAssetLifecycleWithDefaultFile(TestAssetLifecycleBase):

    def setUp(self):
        super().setUp()
        self.create_default_asset()

    def test_fetch_list(self):
        response = self.simulate_get("/corpus/test_corpus/assets")
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.assertEqual(response.json, ["testFile"])

    def test_fetch_info(self):
        m = hashlib.sha512()
        m.update("ハロー・ワールド".encode("utf8"))
        m = m.hexdigest()

        response = self.simulate_get("/corpus/test_corpus/assets/testFile")

        self.assertDictEqual(response.json["metadata"], {"someKey": {"someChildKey": "someValue"}})
        self.assertEqual(response.json["mimeType"], "text/plain")
        self.assertEqual(response.json["typeDescription"], BinaryAssetKind.UTF8_TEXT.value)
        self.assertEqual(response.json["checksum"], m)

        self.assertTrue("id" in response.json)

    def test_fetch_content(self):
        response = self.simulate_get("/corpus/test_corpus/assets/testFile")

        asset_id = response.json["id"]

        response = self.simulate_get("/asset/{}/content".format(asset_id))
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.assertEqual(response.content, "ハロー・ワールド".encode("utf8"))

    def test_delete(self):
        response = self.simulate_delete("/corpus/test_corpus/assets/testFile")
        self.assertEqual(response.status, falcon.HTTP_ACCEPTED)