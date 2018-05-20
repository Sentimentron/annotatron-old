from falcon import testing
import falcon
import hashlib

from pyannotatron.models import Question

from test_asset import TestAssetLifecycleWithDefaultFileBase


class TestQuestion(TestAssetLifecycleWithDefaultFileBase):

    def test_is_initially_empty(self):
        response = self.simulate_get("/corpus/test_corpus/questions")
        self.assertEqual(len(response.json), 0)

    def test_create_retrieve_delete_question(self):
        input_json = {
            "created": "2018-04-23T18:25:43.511000Z",
            "summaryCode": "WORDS",
            "humanPrompt": "Divide this audio file into words",
            "kind": "TimeSeriesSegmentationQuestion",
            "annotationInstructions": "Click between each word",
            "detailedAnnotationInstructions": "So much more to say",
            "maximumSegments": 5,
            "minimumSegments": 1,
            "segmentChoices": ["hi", "world"],
            "freeFormAllowed": True,
            "assets": None,
        }
        question = Question.from_json(input_json)
        response = self.simulate_post("/corpus/test_corpus/questions", json=question.to_json())
        inserted_id = response.json["insertedId"]

        response = self.simulate_get("/corpus/test_corpus/questions/{}".format(inserted_id))
        retrieved = response.json
        retrieved.pop('id', None)
        self.assertDictEqual(retrieved, input_json)

        response = self.simulate_get("/corpus/test_corpus/questions")
        self.assertTrue(inserted_id in response.json)

        response = self.simulate_delete("/corpus/test_corpus/questions/{}".format(inserted_id))
        self.assertEqual(response.status, falcon.HTTP_202)

        response = self.simulate_get("/corpus/test_corpus/questions")
        self.assertFalse(inserted_id in response.json)

