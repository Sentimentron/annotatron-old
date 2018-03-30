from django.core.management.base import BaseCommand
from corpora.models import Corpus
import time


class Command(BaseCommand):
    help = 'Waits for for the postgres database to come online.'

    def add_arguments(self, parser):
        parser.add_argument('max_tries', type=int, default=50)

    def handle(self, *args, **options):
        for tries in range(options['max_tries']):
            try:
                c = Corpus.objects.count()
                print("Found {} corpora, continuing startup".format(c))
                return
            except Exception as ex:
                print("Caught exception {}, waiting for 100ms".format(ex))
                time.sleep(0.1)
