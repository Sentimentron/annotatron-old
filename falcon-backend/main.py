import json
import logging
import random
import string
from datetime import datetime, timedelta
from wsgiref import simple_server

import bcrypt
import falcon
from Crypto.Cipher import ARC4
from pyannotatron.models import ConfigurationResponse, NewUserRequest, ValidationError, FieldError, LoginRequest, \
    LoginResponse, AnnotatronUser, UserKind, Corpus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import User, Token, DbCorpus

Session = sessionmaker()


class TokenController:

    def __init__(self, storage: Session):
        self.storage = storage

    def clean_expired_tokens(self):
        self.storage.query(Token).filter(Token.expires < datetime.utcnow()).delete()

    def remove_tokens_for_user(self, user: User):
        self.storage.query(Token).filter(Token.user_id == user.id).delete()
        self.storage.commit()

    def check_token(self, token) -> bool:
        self.clean_expired_tokens()
        return self.storage.query(Token).filter(Token.expires > datetime.utcnow()).filter_by(token=token).count() == 1

    def get_user_from_token(self, token: str) -> User:
        matches = self.storage.query(Token).filter_by(token=token)
        if matches.count() > 0:
            return matches.first().user

    def get_token_for_user(self, user: User) -> Token:
        self.clean_expired_tokens()
        matches = self.storage.query(Token).filter_by(user_id=user.id)
        if matches.count() > 0:
            return matches.first()

    def get_or_create_token_for_user(self, user: User) -> Token:
        token = self.get_token_for_user(user)
        if not token:
            return self.issue_token(user)
        return token

    def issue_token(self, to_user: User) -> Token:
        key = None
        while True:
            self.storage.begin(subtransactions=True)
            key = ''.join(random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)
            )
            if self.check_token(key):
                self.storage.rollback()
                continue
            t = Token(user_id=to_user.id, expires=datetime.now() + timedelta(days=7), token=key)
            self.storage.add(t)
            self.storage.commit()
            break

        return self.storage.query(Token).filter_by(token=key).first()


class UserController:

    def __init__(self, storage):
        self.storage = storage

    def get_administrators(self):
        users = self.get_all_users().filter_by(role="Administrator")
        for u in users:
            yield u

    def initial_user_created(self) -> bool:
        for user in self.get_administrators():
            logging.debug(user)
            return True
        return False

    def get_user_from_id(self, id: int) -> User:
        return self.get_all_users().filter_by(id=id).first()

    def get_all_users(self):
        return self.storage.query(User).filter_by(deactivated_on=None)

    def check_credentials(self, lr: LoginRequest) -> bool:
        user = self.get_user(lr.username)
        return bcrypt.checkpw(lr.password.encode("utf8"), user.password)

    def get_user(self, username: str) -> User:
        return self.get_all_users().filter_by(username=username).first()

    def _create_user(self, rq: NewUserRequest, reset_needed=False) -> ValidationError:
        # Check for obvious issues like missing fields
        if False:
            errors = rq.check_for_problems()
            if len(errors) > 0:
                return errors

        # Encrypt, salt user password
        password_hash = bcrypt.hashpw(rq.password.encode("utf8"), bcrypt.gensalt())

        u = User(
            username = rq.username,
            role = rq.role.value,
            password = password_hash,
            email=rq.email,
            random_seed=bcrypt.gensalt(),
            password_reset_needed=reset_needed,
            deactivated_on=None,
        )

        self.storage.add(u)
        self.storage.commit()

        #self.storage.add(u)
        #self.storage.commit()
        return None

    def create_user(self, new_user: NewUserRequest, requesting_user: User):
        if requesting_user.role != UserKind.ADMINISTRATOR.value:
            return ValidationError([FieldError("_meta", "requesting user is not administrator", False)])

        return self._create_user(new_user, reset_needed=True)

    def create_initial_user(self, rq) -> ValidationError:
        if self.initial_user_created():
            return ValidationError([FieldError("_state", "initial user already created", False)])

        rq.role = UserKind.ADMINISTRATOR
        return self._create_user(rq, reset_needed=False)

    def change_password(self, user: User, old_password: str, new_password: str, check_password: bool) -> ValidationError:
        if check_password:
            # Check the credentials
            status = bcrypt.checkpw(old_password.encode("utf8"), user.password)
            if not status:
                return ValidationError([FieldError("password", "must match original", False)])

        new_hash = bcrypt.hashpw(new_password.encode("utf8"), bcrypt.gensalt())
        user.password = new_hash
        user.password_reset_needed = not check_password
        self.storage.commit()

        t = TokenController(self.storage)
        t.remove_tokens_for_user(user)


class CorpusController:

    def __init__(self, storage: Session):
        self.storage = storage

    def get_identifiers(self) -> [str]:
        return [x.name for x in self.storage.query(DbCorpus).all()]

    def get_corpus_from_identifier(self, id:str) -> Corpus:
        obj = self.storage.query(DbCorpus).filter_by(name=id).first()
        return Corpus(obj.name, obj.description, obj.created, obj.copyright_usage_restrictions, obj.id)

    def create_corpus(self, c: Corpus):
        c = DbCorpus(
            name=c.name,
            description=c.description,
            copyright_usage_restrictions=c.copyright
        )
        self.storage.add(c)
        self.storage.commit()


class CurrentUserResource:

    def on_get(self, req, resp): #getWhoIAm
        if not req.user:
            resp.status = falcon.HTTP_202
            return resp

        user = AnnotatronUser(username=req.user.username, role=UserKind(req.user.role),
                    created=req.user.created, id=req.obfuscate_int64_field(req.user.id),
                    email=req.user.email)
        resp.media = user


class InitialUserResource:

    """
    Test:
        * Empty database, on_get should return "I need configuration."
        * On post, should accept user response
        * on_get should no longer return "I need configuration."
        * on_post should no longer accept new users
    """

    def on_get(self, req, resp): # checkNeedsSetup
        initial = not UserController(req.session).initial_user_created()
        response = ConfigurationResponse(requires_setup=(initial))
        resp.obj = response
        resp.status = falcon.HTTP_200
        return resp

    def on_post(self, req, resp): # createInitialUser
        u = UserController(req.session)
        rq = NewUserRequest.from_json(req.body)
        errors = u.create_initial_user(rq)
        if errors:
            resp.obj = errors
            resp.status = falcon.HTTP_403
            #resp.status = falcon.HTTPNotAcceptable
        else:
            t = TokenController(req.session)
            user = u.get_user(rq.username)
            token = t.get_or_create_token_for_user(user)
            resp.obj = LoginResponse(token=token.token, password_reset_needed=user.password_reset_needed)
            resp.status = falcon.HTTP_201
        return resp


class WhoAmIResource:

    def on_get(self, req, resp): # getWhoIAm
        obfuscated_id = req.obfuscate_int64_field(req.user.id)
        redirect = "/auth/users/{}".format(obfuscated_id)
        raise falcon.HTTPFound(redirect)


class UserResource:

    def on_get(self, req, resp, id=None): #getUserDetails # listUsers
        if id:
            return self._get_id(req, resp, id)
        return self._get_all(req, resp)

    def _get_all(self, req, resp):
        user_list = UserController(req.session).get_all_users()
        ret = []
        for u in user_list:
            ret.append(req.obfuscate_int64_field(u.id))
        resp.obj = ret

    def _get_id(self, req, resp, id):
        original_id = req.recover_int64_field(id)
        if req.user.role == UserKind.ADMINISTRATOR.value:
            u = UserController(req.session).get_user_from_id(original_id)
            response = AnnotatronUser(
                username=u.username,
                email=u.email,
                role=UserKind(u.role),
                created=u.created,
                id=id,
            )
            resp.obj = response
        elif original_id == req.user.id:
            response = AnnotatronUser(
                username=req.user.username,
                email=req.user.email,
                role=UserKind(req.user.role),
                created=req.user.created,
                id=id,
            )
            resp.obj = response
        else:
            raise falcon.HTTPForbidden()

    def on_post(self, req, resp): #createUser
        u = UserController(req.session)
        rq = NewUserRequest.from_json(req.body)
        errors = u.create_user(rq, req.user)
        if errors:
            resp.obj = errors
            resp.status = falcon.HTTP_403
            # resp.status = falcon.HTTPNotAcceptable
        else:
            t = TokenController(req.session)
            user = u.get_user(rq.username)
            token = t.get_or_create_token_for_user(user)
            resp.obj = LoginResponse(token=token.token, password_reset_needed=user.password_reset_needed)
            resp.status = falcon.HTTP_201
        return resp


class UserPasswordResource:

    def on_put(self, req, resp, id):
        original_id = req.recover_int64_field(id)
        if req.user.role == UserKind.ADMINISTRATOR.value or original_id == req.user.id:
            # User's changing their own password, or they're an administrator
            if "oldPassword" in req.body:
                old_password = req.body["oldPassword"]
            else:
                old_password = None
            new_password = req.body["newPassword"]

            should_check_password = req.user.id == original_id

            u = UserController(req.session)
            user = u.get_user_from_id(original_id)
            errors = u.change_password(user, old_password, new_password, should_check_password)
            if errors:
                resp.obj = errors
                raise falcon.HTTPForbidden()
            resp.status = falcon.HTTP_202
        else:
            raise falcon.HTTPForbidden()


class TokenResource:

    def on_post(self, req, resp):
        u = UserController(req.session)
        t = TokenController(req.session)
        l = LoginRequest.from_json(req.body)

        if u.check_credentials(l):
            user = u.get_user(l.username)
            resp.status = falcon.HTTP_200
            resp.obj = LoginResponse(token=t.get_or_create_token_for_user(user).token, password_reset_needed=user.password_reset_needed)
        else:
            resp.status = falcon.HTTP_403
            resp.media = None
        return resp


class CorpusResource:

    def on_get(self, req, resp, id=None):
        if req.user.role != UserKind.ADMINISTRATOR.value and req.user.role != UserKind.STAFF.value:
            raise falcon.HTTPForbidden("Must be admin or staff")
        c = CorpusController(req.session)
        if not id:
            resp.obj = c.get_identifiers()
        else:
            resp.obj = c.get_corpus_from_identifier(id)

    def on_post(self, req, resp):
        if req.user.role != UserKind.ADMINISTRATOR.value and req.user.role != UserKind.STAFF.value:
            raise falcon.HTTPForbidden("Must be admin or staff")
        c = CorpusController(req.session)
        new_corpus = Corpus.from_json(req.body)
        c.create_corpus(new_corpus)
        resp.status = falcon.HTTP_201


class GetSessionTokenComponent:

    def process_request(self, req, resp):
        auth = req.get_header('Authorization')
        if auth:
            method, _, auth = auth.partition(' ')
            if method != 'Bearer':
                raise falcon.HTTPNotAcceptable('This API only supports Bearer Authorization')

            t = TokenController(req.session)
            req.user = t.get_user_from_token(auth)


class ObfuscationComponent:

    def process_request(self, req, resp):
        # TODO: make me an environmnent variable
        def obfuscate_int64_field(x):
            cipher = ARC4.new("habppootle")
            cipher.encrypt(b'\xbe\x89\xd0\xb1 \xb8\x99\xbd')
            return int.from_bytes(cipher.encrypt((x).to_bytes(8, byteorder='big')), 'big')

        def recover_int64_field(x):
            cipher = ARC4.new("habppootle")
            cipher.encrypt(b'\xbe\x89\xd0\xb1 \xb8\x99\xbd')
            return int.from_bytes(cipher.decrypt((int(x)).to_bytes(8, byteorder='big')), byteorder='big')

        req.obfuscate_int64_field = obfuscate_int64_field
        req.recover_int64_field = recover_int64_field


class AttachSessionComponent:

    def process_request(self, req, resp):
        req.session = Session()


class RequireJSONComponent(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')


class JSONTranslatorComponent(object):
    # NOTE: Starting with Falcon 1.3, you can simply
    # use req.media and resp.media for this instead.

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.body = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        try:
            if resp.obj is not None:
                try:
                    logging.info(json.dumps(resp.obj.to_json()))
                    resp.body = json.dumps(resp.obj.to_json())
                except AttributeError:
                    resp.body = json.dumps(resp.obj)
        except AttributeError:
            pass


def create_app(engine=None):
    if not engine:
        engine = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost/annotatron", echo=True)
    Session.configure(bind=engine)
    app = falcon.API(middleware=[AttachSessionComponent(), JSONTranslatorComponent(), RequireJSONComponent(),
                                 ObfuscationComponent(), GetSessionTokenComponent()])
    app.add_route("/conf/initialUser", InitialUserResource())
    app.add_route("/auth/token", TokenResource())
    app.add_route("/auth/whoAmI", WhoAmIResource())
    app.add_route("/auth/users", UserResource())
    app.add_route("/auth/users/{id}", UserResource())
    app.add_route("/auth/users/{id}/password", UserPasswordResource())
    app.add_route("/corpus", CorpusResource())
    app.add_route("/corpus/{id}", CorpusResource())

    return app

app = create_app()

if __name__ == '__main__':
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()