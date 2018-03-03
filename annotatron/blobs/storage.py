from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import File

import tempfile
import datetime

from .models import Blob


class BlobStorage(Storage):
    """
    All files are stored directly in the database, so that's the only
    thing that needs to be backed up.
    """

    def __init__(self, option=None):
        if not option:
            self.options = settings.CUSTOM_STORAGE_OPTIONS

    def _open(self, name, mode='rb'):
        fp = tempfile.mkstemp()
        blob = Blob.objects.filter(external_id=name).order_by('-inserted_date').first()
        fp.write(blob.blob)
        fp.seek(0, 0)
        return File(fp)

    def _save(self, name, content):
        content.seek(0, 0)
        buffer = content.read()
        blob = Blob.objects.create(external_id=name, blob=buffer, inserted_date=datetime.utcnow())
        blob.save()
        return name

    def exists(self, name):
        blob = Blob.objects.filter(external_id=name)
        return blob.count() > 0

    def get_created_time(self, name):
        blob = Blob.objects.filter(external_id=name)
        first_inserted = blob.order_by('inserted_date').first()
        return first_inserted.inserted_date

    def get_modified_time(self, name):
        blob = Blob.objects.filter(external_id=name)
        first_inserted = blob.order_by('-inserted_date').first()
        return first_inserted.inserted_date

