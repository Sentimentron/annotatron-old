from .models import Corpus, User, Asset, SkinnyAsset

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
            c.server = self
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
        :return: The Corpus, as saved into the database
        """

        to_upload = corpus.to_json()
        url = self.url("v1/corpora/")
        response = requests.post(url, json=to_upload, auth=self.auth)
        if response.status_code != 201:
            print(response.text)
            raise AnnotatronException("POST {}, bad status code {}".format(url, response.status_code), response)
        return self.get_corpus_by_name(corpus.name)

    def add_asset_to_corpus(self, corpus: Corpus, asset: Asset):
        """
        Uploads a given Asset and inserts it into a parent Corpus.
        :param corpus: The Corpus that this Asset will be a part of.
        :param asset: The Asset itself.
        :return: The same Asset.
        """

        to_upload = asset.to_json()
        url = self.url("v1/corpora/{}/".format(corpus.name))
        response = requests.post(url, json=to_upload, auth=self.auth)
        if response.status_code != 201:
            print(to_upload)
            print(response.text)
            raise AnnotatronException("POST {}, bad status code {}".format(url, response.status_code), response)
        return asset

    def retrieve_asset_content(self, corpus: Corpus, asset: Asset):
        """
        Returns the binary content of a given asset.
        """
        url = self.url("v1/corpora/{}/{}".format(corpus.name, asset.name))
        response = requests.get(url, auth=self.auth)
        if response.status_code != 200:
            #print(response.status_code)
            #print(response.text)
            raise AnnotatronException("GET {}, bad status code {}".format(url, response.status_code), response)
        return response.content


    def list_assets_in_corpus(self, corpus: Corpus):
        """
        Retrieves all assets in a given corpus.
        :param corpus: The corpus to query.
        :return: A generator which yields all the Assets inside the corpus.
        """
        url = self.url("v1/corpora/{}/".format(corpus.name))
        response = requests.get(url, auth=self.auth)
        if response.status_code != 200:
            #print(response.text)
            raise AnnotatronException("GET {}, bad status code {}".format(url, response.status_code), response)
        for item in response.json():
            r1 = lambda a, c=corpus, provider=self: provider.retrieve_asset_content(c, a)
            yield SkinnyAsset.from_json(r1, item)
