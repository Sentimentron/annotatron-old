from django.db import models


# Create your models here.
class Corpus(models.Model):
    """
    A Corpus is a collection of Assets
    """
    name = models.TextField(unique=True, null=False)
    description = models.TextField()
    # This question generator field consists of Python which is piped
    # through an OpenFAAS service to generate Question objects attached to
    # this corpora's assets.
    question_generator = models.TextField()

    class Meta:
        managed = False
        db_table = "an_corpora"
        app_label = "corpora"


class Asset(models.Model):

    name = models.TextField(unique=True, null=False)
    kind = models.TextField(null=False)
    mime_type = models.TextField(null=False)
    binary_content = models.BinaryField(null=False)
    date_uploaded = models.DateField(null=False, auto_now_add=True)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name='assets')

    class Meta:
        managed = False
        db_table = "an_assets"
