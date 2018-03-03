from django.db import models


class Blob(models.Model):
    """
    Binary representation of an asset, stored in the database.
    """
    external_id = models.TextField()
    blob = models.BinaryField(null=False)
    date_inserted = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "an_blobs"
        app_label = "blobs"
