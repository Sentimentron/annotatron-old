from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth import get_user_model

ANNOTATION_SOURCES = (
    (1, 'reference'),
    (2, 'user'),
    (3, 'system'),
)


# Create your models here.
class Corpus(models.Model):
    """
        A Corpus is a collection of Assets.
    """
    name = models.TextField(unique=True, null=False)
    description = models.TextField(blank=True)

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
    date_uploaded = models.DateTimeField(null=False, auto_now_add=True)
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


class Annotator(models.Model):
    """
        An Annotator is Annotatron's extension to Django's user object
    """
    external = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created = models.DateTimeField(null=False, auto_now_add=True)

    class Meta:
        managed = False
        db_table = "an_annotators"


class Annotation(models.Model):
    """
        An Annotation is a piece of JSON data attached to an Asset. There are three main kinds:

            "reference" annotations come from the original dataset
            "user" annotations come from Annotatron's interface
            "system" annotations come from summary functions and other automatic activity.

        Annotations also can come in several different kinds. Whilst "kind" can be set to anything
        (provided the front-end can display it), the in-built and validated ones are "text" (which
        can describe both free-form and multiple-choice input) and "1d_segmentation", which is where
        users are asked to segment an audio waveform into non-overlapping ranges.

        Summary functions handle pre-grouped Annotation data. Data is grouped with the source, then
        the summary code. Attempts to mix multiple kinds will trigger a warning.
    """

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=False, related_name='annotations')
    kind = models.TextField(null=False)
    summary_code = models.TextField(null=False)
    data = JSONField(null=False)
    # Keyed as 0 = reference, 1 = user, 2 = system
    source = models.PositiveSmallIntegerField(null=False, choices=ANNOTATION_SOURCES)
    created = models.DateTimeField(null=False, auto_now_add=True)
    annotator = models.ForeignKey(Annotator, on_delete=models.SET_NULL, null=True)
    metadata = JSONField(null=True)

    class Meta:
        managed = False
        db_table = "an_annotations"

