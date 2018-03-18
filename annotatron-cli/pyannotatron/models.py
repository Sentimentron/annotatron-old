import requests
import copy
import base64
import hashlib
import os
import mimetypes
import tempfile
import numbers


class ConfigurationResponse:
    """
        Contains information about whether Annotatron's ready to use, or whether it requires
        further information.
    """

    def __init__(self, requires_setup:bool):
        self.requires_setup = requires_setup

    @classmethod
    def from_json(cls, json):
        return ConfigurationResponse(**json)


class Corpus:
    """
        Represents Annotatron's concept of a corpus, which is a collection of Assets.
    """

    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.server = None

    def to_json(self) -> dict:
        """
        Converts this object to an API-compatible form.
        :return: A dict, ready for conversion to JSON.
        """

        ret = {"name": self.name}
        if self.description is not None:
            ret["description"] = self.description

        return ret

    @classmethod
    def from_json(cls, dict):
        dict = copy.deepcopy(dict)
        dict.pop('id', None)
        return Corpus(**dict)


class User:
    """
        Represents Annotatron's concept of a user, which is used to authenticate
        access to an Annotatron system.
    """

    def __init__(self, username, password, email=None, super_user=False, staff_user=False):
        self.username = username
        self.password = password
        self.email = email
        self.super_user = super_user
        self.staff_user = staff_user

    def to_json(self):
        """
        Converts this object into an API-compatible form.
        :return:
        """
        return {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "is_superuser": self.super_user,
            "is_staff": self.staff_user
        }

    def check_for_issues(self):
        ret = []
        if self.email is None:
            ret.append("email is None")
        return ret

    @classmethod
    def from_json(cls, dict):
        dict = copy.deepcopy(dict)
        dict["super_user"] = dict["is_superuser"]
        dict["staff_user"] = dict["is_staff"]
        dict.pop("is_superuser", None)
        dict.pop("is_staff", None)
        return User(**dict)


class Asset:
    """
        Represents Annotatron's idea of a document, stored in a Corpus.
    """

    def __init__(self, name=None, content:bytes=None, mime_type=None, kind=None, sha_512_sum=None, metadata=None, corpus:Corpus=None):
        """
        Raw constructor for an Asset, probably one that's about to be uploaded.
        :param name: This is a key, unique from all other identifiers for assets in this corpus, used to retrieve this
                     item later.
        :param content: The contents, as a byte string.
        :param mime_type: Optional MIME type, link 'text/plain'
        :param kind: 'audio', 'text', 'video' etc
        :param sha_512_sum: The SHA512 checksum of contents.
        :param metadata: An arbitrary JSON-encodable dictionary of extra information.
        :param id: The upstream identifier.
        """
        self.name = name
        self.mime_type = mime_type
        self.kind = kind
        self.sha_512_sum = sha_512_sum
        self.metadata = metadata
        self.corpus = corpus
        try:
            self.content = content
        except AttributeError:
            # Being called as part of a SkinnyAsset construction.
            pass # Gulp!

    def to_json(self, skinny=False) -> dict:
        """
        Converts this Asset to a JSON representation for Annotatron's API.
        :return: The dict representation.
        """
        ret = {
            "name": self.name,
            "mime_type": self.mime_type,
            "kind": self.kind,

            "metadata": self.metadata,
            "sha_512_sum": self.sha_512_sum
        }

        if not skinny:
            ret["content"] = base64.standard_b64encode(self.content).decode("utf8")

        return ret

    def check_for_problems(self) -> (bool, list):
        """
        Checks for common problems which might prevent Annotatron from processing this Asset.
        :return: (will_work, report), a pair of values. if will_work is False, then Annotatron definitely won't process
                  the Asset correctly. The report contains a list of human-readable strings that describe potential
                  problems.
        """
        will_work, ret = True, []
        if self.kind != "audio":
            if self.kind is None:
                ret.append("kind appears to be None")
                will_work = False
            else:
                ret.append('"audio" is the only understood type for now, the store will succeed, but nothing'
                           ' can display it')
        else:
            if self.mime_type != "audio/x-wav":
                ret.append("mimetype='audio/x-wav' will work best")

        if self.content is None:
            will_work = False
            ret.append("content appears to be blank")

        if self.sha_512_sum is None:
            will_work = False
            ret.append("sha_512_sum is blank")

        if self.mime_type is None:
            ret.append("mimetype is blank, may cause issues downloading the asset later")

        if len(self.content) is None:
            will_work = False
            ret.append("content appears to have no length")

        return will_work, ret

    @classmethod
    def _from_bytes_and_file(cls, content, path_to_file, name=None, cannot_be_text=True, encoding=None, metadata=None,
                             kind=None):

        if isinstance(content, str):
            raise AssertionError("content: should be utf-8 coded bytes (for text), or bytes (for binary)")

        base_name, extension = os.path.splitext(os.path.basename(path_to_file))
        if name is None:
            name = base_name

        mimetype, detected_encoding = mimetypes.guess_type(path_to_file)
        if encoding is None and detected_encoding:
            encoding = detected_encoding
        if mimetype == "text/plain" and encoding is not None:
            mimetype = "text/plain; charset={}".format(encoding)

        if kind is None:
            if extension in [".wav", ".mp3", ".aac", ".mp4"]:
                kind = "audio"
            elif extension in [".txt"]:
                if cannot_be_text:
                    raise AssertionError("Make sure you didn't mean to use from_txt_file")
                kind = "text"
            else:
                kind = None

        checksummer = hashlib.sha512()
        checksummer.update(content)
        checksum = checksummer.hexdigest()

        return Asset(name, content, mimetype, kind, checksum, metadata)

    @classmethod
    def from_bytes(cls, content, name=None, metadata=None, kind=None):
        """
        Generates a new Asset from a raw byte string. Writes the string temporarily to disk for MIME detection.
        It's strongly recommended to use a method like :from_binary_file: or :from_text_file: instead.
        :param content: The content of this Asset, as a byte string.
        :param name: A unique key that identifies this Asset.
        :param metadata: JSON-serializable metadata.
        :param kind: 'audio', 'video' etc.
        :return: The constructed Asset.
        """
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(content)
            return cls._from_bytes_and_file(content, fp.name, name, True, None, metadata, kind)

    @classmethod
    def from_binary_file(cls, path_to_file, name=None, metadata=None, kind=None):
        """
        Generates a new Asset from a binary file on disk.
        :param path_to_file: The file to convert.
        :param name: A unique name for this asset.
        :param metadata: JSON-serializable metadata.
        :param kind: 'audio' etc.
        :return: The constructed Asset.
        """
        with open(path_to_file, "rb") as fp:
            content = fp.read()
            return cls._from_bytes_and_file(content, path_to_file, name, cannot_be_text=True, metadata=metadata,
                                            kind=kind)

    @classmethod
    def from_text_file(cls, path_to_file:str, name=None, encoding="utf8", metadata=None):
        """
        Generates a new Asset from a text file on disk.
        :param path_to_file: The file to convert.
        :param name: A unique key for this item.
        :param encoding: e.g. "utf8". Annotatron will store and handle the Asset using this encoding.
        :param metadata: JSON-serializable metadata.
        :return: The constructed Asset.
        """
        with open(path_to_file, "r", encoding=encoding) as fp:
            content = fp.read().encode(encoding)
            return cls._from_bytes_and_file(content, path_to_file, name, cannot_be_text=False, encoding="utf8",
                                            metadata=metadata)


    @classmethod
    def from_json(cls, dict, corpus=None):
        """
        Constructs a new Asset from its remote representation.
        :param dict: The JSON to parse.
        :return: The constructed Asset.
        """
        dict = copy.deepcopy(dict)
        dict['content'] = base64.standard_b64decode(dict['content'])
        dict['corpus'] = corpus
        return Asset(**dict)


class SkinnyAsset(Asset):
    """
        Placeholder for a full Asset, retrieves content etc from Annotatron.
    """

    def __init__(self, content_callback, **kwargs):
        super(SkinnyAsset, self).__init__(**kwargs)
        self._content = None
        self._content_callback = content_callback

    @property
    def content(self):
        if self._content:
            return self._content
        self._content = self._content_callback(self)
        return self._content

    @classmethod
    def from_json(cls, content_callback, dict, corpus):
        dict = copy.deepcopy(dict)
        dict["corpus"] = corpus
        return SkinnyAsset(content_callback, **dict)


class Annotation:
    """
        An Annotation is a lump of JSON attached to an Asset. They can be in response
        to a question.
    """

    def __init__(self, asset: Asset, summary_code: str, data: object, kind: str, source: str, metadata: object):
        """
        Create an Annotation object, which tells us something about an Asset.
        :param asset: The Asset we're annotating.
        :param summary_code: This is used to group and summarize responses from multiple annotators.
        :param data: JSON-serializable data that comprises the annotation.
        :param kind: e.g. "text", "segmentation_1d", "range_1d" etc.
        :param source: Either "reference" or "human"
        :param metadata: Anything that's not directly related to the annotation's data (JSON-serializable).
        """

        self.asset = asset
        self.summary_code = summary_code
        self.data = data
        self.kind = kind
        self.source = source
        self.metadata = metadata

    def check_for_problems(self) -> (bool, list):
        """
        Validates this Annotation for problems that may stop Annotatron from processing it.
        :return: A tuple (might_work, problems). If might_work is False, there's definitely a problem.
         If might_work is True, there still may be a problem.
        """
        might_work = True
        errors = []
        if self.asset is None:
            might_work = False
            errors.append("asset: cannot be None")
        if self.asset.name is None:
            might_work = False
            errors.append("asset.name: cannot be None")
        if self.asset.corpus is None:
            might_work = False
            errors.append("asset.corpus: cannot be None")
        if not isinstance(self.asset.corpus, Corpus):
            might_work = False
            errors.append("asset.corpus: must be a Corpus")
        if self.summary_code is None:
            might_work = False
            errors.append("summary_code: cannot be None")
        if self.data is None:
            might_work = False
            errors.append("data: cannot be None")
        if self.kind is None:
            might_work = False
            errors.append("kind: cannot be None")
        if self.source is None:
            might_work = False
            errors.append("source: cannot be None")

        valid_kinds = ["text", "1d_segmentation"]
        if self.kind not in valid_kinds:
            errors.append("kind: unrecognized (choose from '%s')".format(",".join(valid_kinds)))

        if self.kind == "text":
            if not isinstance(self.data, str):
                errors.append("data: format for 'text' should be a string")
        elif self.kind == "1d_segmentation":
            if not isinstance(self.data, list):
                errors.append("1d_segmentation: format for '1d_segmentation' should be a list")
            else:
                for elem in self.data:
                    failed_numeric_check = False
                    if not isinstance(elem, numbers.Integral):
                        failed_numeric_check = True
                    if failed_numeric_check:
                        errors.append("1d_segmentation: format for '1d_segmentation' should be a list of numbers")

        valid_sources = ["reference", "user", "summary"]
        if self.source not in valid_sources:
            errors.append("source: unrecognized (choose from '%s')".format(",".join(valid_sources)))

        return might_work, errors

    def to_json(self) -> dict:
        return {
            "asset": self.asset.to_json(skinny=False),
            "corpus": self.asset.corpus.to_json(),
            "summary_code": self.summary_code,
            "data": self.data,
            "kind": self.kind,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_json(cls, js):

        corpus = Corpus.from_json(js["corpus"])
        js.pop('corpus', None)
        js["asset"] = SkinnyAsset.from_json(content_callback=None, dict=js["asset"], corpus=corpus)

        return cls(**js)


class QuestionPlaceHolder:
    """
        This is a class which can be converted into a proper question by Annotatron.
    """
    def __init__(self, summary_code):
        self.summary_code = summary_code

    def to_json(self) -> str:
        return self.summary_code

    @classmethod
    def from_json(cls, summary):
        return QuestionPlaceHolder(summary)


class QuestionDefaultAnswerSource:
    """
        This is a class which describes where a Question should get a default property or
        predefined answer from.
    """
    def __init__(self, default_answer=None):
        self.default_answer = default_answer
        pass

    def to_json(self) -> dict:
        """
        Converts this object into an API-ready input.
        """
        if self.default_answer:
            return {
                "default": self.default_answer
            }
        else:
            return {}

    @classmethod
    def from_json(cls, dict):
        return cls(**dict)


class QuestionDefaultFromOtherQuestion(QuestionDefaultAnswerSource):
    """
        This is a class which indicates that a Question should get a default property from
        a user's previous input on another question.
    """
    def __init__(self, previous_question: QuestionPlaceHolder, best_known=False, reference=False):
        """
        Specifies that the Question's state should be pre-populated from the answer to another Question.
        :param previous_question: The previous Question's summary code.
        :param best_known: Whether the answer should be taken as an aggregation of best known results.
                          e.g. "What are the words spoken within each segment of the above file?"
        :param reference: Whether the answer should be taken from a known-good (or reference) result if possible.
                          e.g. "Is this transcription accurate?"

                          If this and best_known are both True, then reference will win if it's available.
        """
        super().__init__(None)
        self.previous_question = previous_question
        self.reference = reference
        self.best_known = best_known

    def to_json(self) -> dict:
        """
        Converts this object into an API-ready input.
        """
        ret = {
            "question": self.previous_question.to_json(),
            "best_known": self.best_known,
            "reference": self.reference
        }
        return ret

    @classmethod
    def from_json(cls, d):
        d = copy.deepcopy(d)
        d["question"] = QuestionPlaceHolder.from_json()
        return cls(**d)


class Question:
    """
        A Question is a task that a User must provide an answer for, it's attached to an Asset.
        Different Assets inside a Corpora can have different questions depending on what they are.
    """
    def __init__(self, summary_code, question_text, question_kind,
                 default_answer : QuestionDefaultAnswerSource = None):
        """
        Creates a new Question object.
        :param summary_code: When the "best known annotation" method is called, the method will be provided with a dict
                             like the following:
                             {
                                "summary_code": [user_annotation_1, user_annotation_2]
                             }
                             Changing this is what makes the Question separable from other questions.
        :param question_text: This is the human-readable text that can will be entered.
        :param question_kind: This describes the format of the question, e.g. 'segmentation'
                              Not all combinations of question_kind and Asset are supported
                              (see :check_for_problems:).
        :param default_answer: Describes some state that can initialize a question.
        """
        self.code = summary_code
        self.text = question_text
        self.kind = question_kind
        self.default = default_answer

    def to_json(self) -> dict:
        return {
            "summary_code": self.code,
            "question_text": self.text,
            "question_kind": self.kind,
            "default_answer": self.default.to_json()
        }

    @classmethod
    def from_json(cls, d):
        d = copy.deepcopy(d)
        if "default" in d["default_answer"].keys():
            d["default_answer"] = QuestionDefaultAnswerSource.from_json(d["default_answer"])
        else:
            d["default_answer"] = QuestionDefaultFromOtherQuestion.from_json(d["default_answer"])
        return Question(**d)
