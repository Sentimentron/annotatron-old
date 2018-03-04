from models import Corpus, User
from utils import url

import requests
from requests.auth import HTTPBasicAuth


class AnnotatronException(Exception):

    def __init__(self, help_text, response):
        super().__init__(help_text)
        self.response = response


class Annotatron:
    """
        Represents a connection to an Annotatron server.
    """

    def __init__(self, url, user: User=None, auth: HTTPBasicAuth = None):
        if not auth:
            self.auth = HttpBasicAuth(user.username, user.password)
        else:
            self.auth = auth
        # TODO: validate this
        self.url_base = url
        assert self.url_base is not None

    def __iter__(self):
        """
            Returns the Corpus objects on the server, one by one.
            :return: A Corpus object, or none if none are found
        """
        r = requests.get(self.url("v1/corpora/"), auth=self.auth)
        if r.status_code != 200:
            raise AnnotatronException("Couldn't list corpora", r)

        l = r.json()
        for item in l:
            c = Corpus.from_json(item)
            yield c

    def url(self, path) -> str:
        return self.url_base + path

    def get_corpus_by_name(self, name) -> Corpus:
        """
        Looks up a corpus within the Annotatron server.
        :param name: The name to look for.
        :return: Returns a matching Corpus object, or None if it does not exist.
        """
        for c in self:
            if c.name == name:
                return c
        return None

    def send_corpus(self, corpus: Corpus):
        """
        Saves a Corpus into Annotatron
        :param corpus: The Corpus to save.
        :return: Nothing, doesn't throw an exception if the op succeeds.
        """

        to_upload = corpus.to_json()
        url = self.url("v1/corpora/")
        response = requests.post(url, json=to_upload, auth=self.auth)
        if response.status_code != 201:
            print(response.text)
            raise AnnotatronException("POST {}, bad status code {}".format(url, response.status_code), response)

