from django.db import models
from django.contrib.postgres.fields import JSONField


# Create your models here.
class Corpus(models.Model):
    """
        A Corpus is a collection of Assets.
    """
    name = models.TextField(unique=True, null=False)
    description = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = "an_corpora"
        app_label = "corpora"


class Asset(models.Model):
    """
        An Asset is an indivisable binary blob which can be annotated.
    """

    # This is a human-readable name for this individual asset.
    name = models.TextField(null=False)
    # This can be anything, but is normally "audio", "image" or similar.
    kind = models.TextField(null=False)
    # This contains the detected mime_type for the file.
    mime_type = models.TextField(null=False)
    # This contains the actual content of the asset. It's verified via the :sha_512_sum: field.
    binary_content = models.BinaryField(null=False)
    # This contains the date Annotatron became aware of the asset.
    date_uploaded = models.DateField(null=False, auto_now_add=True)
    # This field links the Asset with the Corpus it's a member of
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name='assets')
    # This contains the human-readable hash of binary_content, enforced at the database level.
    sha_512_sum = models.TextField(null=False)
    # This field contains information provided by the user on upload that isn't part of the Asset itself
    metadata = JSONField(null=True)

    class Meta:
        managed = False
        db_table = "an_assets"
        unique_together = (("name", "corpus"),)
