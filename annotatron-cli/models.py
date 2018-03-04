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
