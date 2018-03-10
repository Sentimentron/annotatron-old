import requests
import copy
import base64
import os
import mimetypes

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

    def __init__(self, name=None, content:bytes=None, mime_type=None, kind=None):
        self.name = name
        self.mime_type = mime_type
        self.kind = kind
        try:
            self.content = content
        except AttributeError:
            # Being called as part of a SkinnyAsset construction.
            pass # Gulp!


    def to_json(self) -> dict:
        return {
            "name": self.name,
            "mime_type": self.mime_type,
            "kind": self.kind,
            "content": base64.standard_b64encode(self.content).decode("utf8")
        }

    def check_for_problems(self, ann_instance=None) -> (bool, list):
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

        if len(self.content) is None:
            will_work = False
            ret.append("content appears to have no length")

        return will_work, ret

    @classmethod
    def from_bytes(cls, content, path_to_file, name=None, cannot_be_text=True, encoding=None):
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
        print(mimetype)
        if extension in [".wav", ".mp3", ".aac", ".mp4"]:
            kind = "audio"
        elif extension in [".txt"]:
            if cannot_be_text:
                raise AssertionError("Make sure you didn't mean to use from_txt_file")
            kind = "text"
        else:
            kind = None
        return Asset(name, content, mimetype, kind)

    @classmethod
    def from_binary_file(cls, path_to_file, name=None):
        with open(path_to_file, "rb") as fp:
            content = fp.read()
            return cls.from_fp(content, path_to_file, name, cannot_be_text=True)

    @classmethod
    def from_text_file(cls, path_to_file, encoding="utf8", name=None):
        with open(path_to_file, "r", encoding=encoding) as fp:
            content = fp.read().encode(encoding)
            return cls.from_bytes(content, path_to_file, name, cannot_be_text=False, encoding="utf8")


    @classmethod
    def from_json(cls, dict):
        dict = copy.deepcopy(dict)
        dict['content'] = base64.standard_b64decode(dict['content'])
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
    def from_json(cls, content_callback, dict):
        dict = copy.deepcopy(dict)
        print(dict)
        return SkinnyAsset(content_callback, **dict)


class Corpus:
    """
        Represents Annotatron's concept of a corpus, which is a collection of Assets.
    """

    def __init__(self, name, description=None, question_generator=None):
        self.name = name
        self.description = description
        self.question_generator = question_generator
        self.server = None

    def to_json(self) -> dict:
        """
        Converts this object to an API-compatible form.
        :return: A dict, ready for conversion to JSON.
        """

        ret = {"name": self.name}
        if self.description is not None:
            ret["description"] = self.description
        if self.question_generator is not None:
            ret["question_generator"] = self.question_generator

        return ret

    @classmethod
    def from_json(cls, dict):
        dict = copy.deepcopy(dict)
        dict.pop('id', None)
        return Corpus(**dict)


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
