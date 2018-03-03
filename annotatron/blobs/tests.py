import os
from django.test import TestCase

from blobs.storage import BlobStorage


class BlobStorageTest(TestCase):

    def setUp(self):
        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file_1 = os.path.join(self.dir, 'test_1.txt')
        self.test_file_2 = os.path.join(self.dir, 'test_2.txt')

    def testInsert(self):
        b = BlobStorage()
        content = None
        with open(self.test_file_1, 'rb') as fp:
            b.content = fp.read()
            b.save('test', fp)

        created1 = b.get_created_time('test')
        updated1 = b.get_modified_time('test')

        self.assertEqual(created1, updated1)

        fp = b.open('test')
        new_content = fp.read()
        self.assertEqual(content, new_content)

    def testMultipleInsert(self):
        b = BlobStorage()
        with open(self.test_file_1, 'rb') as fp:
            b.save('test', fp)

        created1 = b.get_created_time('test')
        updated1 = b.get_modified_time('test')

        self.assertEqual(created1, updated1)

        expected_content = None
        with open(self.test_file_2, 'rb') as fp:
            expected_content = fp.read()
            b.save('test', fp)

        created2 = b.get_created_time('test')
        updated2 = b.get_updated_time('test')

        self.assertGreater(updated2, created2)

        current_content = b.open('test').read()
        self.assertEqual(expected_content, current_content)

