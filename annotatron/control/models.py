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
    corpus = models.ForeignKey(Corpus, on_delete='cascade')
    # The unique_id of an asset corresponds to something the user can set
    unique_id = models.TextField(unique=True)
    # Kind refers to what this file is
    kind = models.TextField(choices=[("audio", "An audio file for audio_segmentation tasks")], null=False)
    # Stores the actual type of the file
    mime_type = models.TextField(null=False)
    # Binary content stores the type of the asset
    binary_content = models.BinaryField(null=False)

    class Meta:
        managed = False
        db_table = "an_assets"


class Question(models.Model):

    unique_id = models.TextField(unique=True)
    asset_id = models.ForeignKey(Asset, on_delete='cascade')

    class Meta:
        managed = False
        db_table = "an_questions"
