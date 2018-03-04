import requests
import copy


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

    @classmethod
    def from_json(cls, dict):
        dict = copy.deepcopy(dict)
        dict["super_user"] = dict["is_superuser"]
        dict["staff_user"] = dict["is_staff"]
        dict.pop("is_superuser", None)
        dict.pop("is_staff", None)
        return User(**dict)

class Corpus:
    """
        Represents Annotatron's concept of a corpus, which is a collection of Assets.
    """

    def __init__(self, name, description=None, question_generator=None):
        self.name = name
        self.description = description
        self.question_generator = question_generator

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
