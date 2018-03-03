from django.db import models

# Create your models here.

class Corpus(models.Model):

    name = models.TextField(unique=True, null=False)
    # This question generator field consists of Javascript which is piped
    # through an OpenFAAS service to generate Question objects attached to
    # this corpora's assets.
    question_generator = models.TextField()

    class Meta:
        managed = False
        db_table = "an_corpora"

class Asset(models.Model):
    corpus_id = models.ForeignKey(Corpus, on_delete='cascade')
    # The unique_id of an asset corresponds to
    unique_id = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = "an_assets"


class Question(models.Model):

    unique_id = models.TextField(unique=True)
    asset_id = models.ForeignKey(Asset, on_delete='cascade')

    class Meta:
        managed = False
        db_table = "an_questions"
