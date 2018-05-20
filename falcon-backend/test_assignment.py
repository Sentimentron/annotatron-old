from falcon import testing
import falcon
import hashlib

from pyannotatron.models import Question

from test_asset import TestAssetLifecycleWithDefaultFileBase


class TestAssignmentLifecycle(TestAssetLifecycleWithDefaultFileBase):

    def test_is_initially_empty(self):
        user_id = self.get_current_user_id()
        response = self.simulate_get("/assignments/byUser/{}".format(user_id))
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.assertEqual(len(response.json["forReview"]), 0)
        self.assertEqual(len(response.json["forAnnotation"]), 0)

    def test_assignment_lifecycle_no_reviewer(self):
        user_id = self.get_current_user_id()
        question_input_json = {
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

        response_input_json = {
            "created": "2018-04-23T18:25:43.511000Z",
            "kind": "TimeSeriesSegmentationAnnotation",
            "source": "Human",
            "summaryCode": "WORDS",
            "segments": [
                0.1, 2.0
            ],
            "annotations": [
                "hello", "world"
            ]
        }

        assignment_json = {
            "assets": [1, 22],
            "assignedUserId": user_id,
            "assignedAnnotatorId": user_id,
            "question": question_input_json,
        }

        # Create the assignment, assigned to the current admin user as annotator and reviewer
        response = self.simulate_post("/assignments/test_corpus/", json=assignment_json)
        inserted_id = response.json["insertedId"]

        # Should appear in our to-do list
        response = self.simulate_post("/assignments/byUser/{}".format(user_id))
        self.assertTrue(inserted_id in response.json["forAnnotation"])

        # Should appear in the right section of the Corpus annotations
        response = self.simulate_get("/assignments/test_corpus/")
        self.assertTrue(inserted_id in response.json["forAnnotation"])

        # Provide a response, should be automatically finalized
        response = self.simulate_get("/assignments/{}".format(inserted_id))
        editing = response.json
        editing['response'] = response_input_json
        editing['annotatorNotes'] = 'Huh?'
        response = self.simulate_patch("/assignments/{}".format(inserted_id))
        self.assertEquals(response.status_code, falcon.HTTP_ACCEPTED)

        # Should appear in the completed setion
        response = self.simulate_get("/assignments/test_corpus/")
        self.assertTrue(inserted_id in response.json["completed"])

    """
    def test_assignment_lifeycle(self):
        # TODO: switch this case on
        # TODO: we have to make sure in this case that the reviewer and the annotator are different people
        user_id = self.get_current_user_id()

        question_input_json = {
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

        response_input_json = {
            "created": "2018-04-23T18:25:43.511000Z",
            "kind": "TimeSeriesSegmentationAnnotation",
            "source": "Human",
            "summaryCode": "WORDS",
            "segments": [
                0.1, 2.0
            ],
            "annotations": [
                "hello", "world"
            ]
        }

        assignment_json = {
            "assets": [1, 22],
            "assignedUserId": user_id,
            "assignedAnnotatorId": user_id,
            "question": question_input_json,
            "response": None,
            "assignedReviewerId": user_id
        }

        # Create the assignment, assigned to the current admin user as annotator and reviewer
        response = self.simulate_post("/assignments/test_corpus/", json=assignment_json)
        inserted_id = response.json["insertedId"]

        # Should appear in our to-do list
        response = self.simulate_post("/assignments/byUser/{}".format(user_id))
        self.assertTrue(inserted_id in response.json["forAnnotation"])
        
        # Should appear in the right section of the Corpus annotations
        response = self.simulate_get("/assignments/test_corpus/")
        self.assertTrue(inserted_id in response.json["forAnnotation"])
        
        # Provide a response and assign it back to the reviewer        
        response = self.simulate_get("/assignments/{}".format(inserted_id))
        editing = response.json
        editing['response'] = response_input_json
        # TODO: should check whether we can just put anybody in here
        editing['assignedUserId'] = editing['assignedReviewerId']
        editing['annotatorNotes'] = 'Huh?'
        response = self.simulate_patch("/assignments/{}".format(inserted_id))
        self.assertEquals(response.status_code, falcon.HTTP_ACCEPTED)

        # Initially, reviewer rejects with some notes
        response = self.simulate_post("/assignments/byUser/{}".format(user_id))
        self.assertTrue(inserted_id in response.json["forReview"])
        response = self.simulate_get("/assignments/{}".format(inserted_id))
        editing = response.json
        self.assertEquals(editing['annotator_notes'], 'Huh?')
        editing['reviewerNotes'] = "What?"
        editing['assignedUserId'] = editing['assignedAnnotatorId']
        response = self.simulate_patch("/assignments/{}".format(inserted_id))
        self.assertEquals(response.status_code, falcon.HTTP_ACCEPTED)
        
        # User goes back and corrects...
        response = self.simulate_get("/assignments/{}".format(inserted_id))
        editing = response.json
        editing['response'] = response_input_json
        # TODO: should check whether we can just put anybody in here
        editing['assignedUserId'] = editing['assignedReviewerId']
        editing['annotatorNotes'] = 'OK?'
        editing['created'] = datetime.utcnow()
        response = self.simulate_patch("/assignments/{}".format(inserted_id))
        self.assertEquals(response.status_code, falcon.HTTP_ACCEPTED)

        # Reviewer accepts
        response = self.simulate_post("/assignments/byUser/{}".format(user_id))
        self.assertTrue(inserted_id in response.json["forReview"])
        response = self.simulate_get("/assignments/{}".format(inserted_id))
        editing = response.json
        self.assertEquals(editing['annotator_notes'], 'Huh?')
        editing['reviewerNotes'] = "OK"
        editing['assignedUserId'] = editing['assignedAnnotatorId']
        
        response = self.simulate_patch("/assignments/{}".format(inserted_id))
        self.assertEquals(response.status_code, falcon.HTTP_ACCEPTED)
        
        # TODO: make sure this appears in the Corpus' approved list.
        
        """
