from django.db import models


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

    name = models.TextField(unique=True, null=False)
    kind = models.TextField(null=False)
    mime_type = models.TextField(null=False)
    binary_content = models.BinaryField(null=False)
    date_uploaded = models.DateField(null=False, auto_now_add=True)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name='assets')

    class Meta:
        managed = False
        db_table = "an_assets"
