from django.db import models


# Create your models here.
class Corpus(models.Model):

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