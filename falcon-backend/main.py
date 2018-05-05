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
    LoginResponse, AnnotatronUser, UserKind
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import User, Token

Session = sessionmaker()


class TokenController:

    def __init__(self, storage: Session):
        self.storage = storage

    def clean_expired_tokens(self):
        self.storage.query(Token).filter(Token.expires < datetime.utcnow()).delete()

    def check_token(self, token) -> bool:
        self.clean_expired_tokens()
        return self.storage.query(Token).filter(Token.expires > datetime.utcnow()).filter(token=token).count() == 1

    def get_user_from_token(self, token: str) -> User:
        matches = self.storage.query(Token).filter_by(token=token)
        if matches.count() > 0:
            return matches.first()

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
            with self.storage.transaction() as tx:
                key = ''.join(random.choice(
                    string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)
                )
                if self.check_token(key):
                    continue
                t = Token(user=to_user, expires=datetime.now() + timedelta(days=7), token=key)
                t.save()
                tx.commit()
                break

        return self.storage.query(Token).get(token=key)


class UserController:

    def __init__(self, storage):
        self.storage = storage

    def get_administrators(self):
        return self.storage.query(User).filter_by(role='Administrator')

    def initial_user_created(self) -> bool:
        for user in self.get_administrators():
            logging.debug(user)
            return True
        return False

    def check_credentials(self, lr: LoginRequest) -> bool:
        user = self.storage.query(User).filter_by(username=lr.username).first()
        return bcrypt.checkpw(lr.password, user.password)

    def get_user(self, username: str) -> User:
        return self.storage.query(User).filter_by(username=username).first()

    def _create_user(self, rq: NewUserRequest) -> ValidationError:
        # Check for obvious issues like missing fields
        if False:
            errors = rq.check_for_problems()
            if len(errors) > 0:
                return errors

        # Encrypt, salt user password
        password_hash = bcrypt.hashpw(rq.password.encode("utf8"), bcrypt.gensalt())

        u = User(
            username = rq.username,
            role = rq.role,
            password = password_hash,
            email=rq.email
        )

        self.storage.add(u)
        self.storage.commit()

        #self.storage.add(u)
        #self.storage.commit()
        return None

    def create_initial_user(self, rq) -> ValidationError:
        if self.initial_user_created():
            return ValidationError([FieldError("_state", "initial user already created", False)])

        rq.role = "Administrator"
        return self._create_user(rq)


class CurrentUserResource:

    def on_get(self, req, resp): #getWhoIAm
        if not req.user:
            resp.status = falcon.HTTP_202
            return resp

        user = AnnotatronUser(username=req.user.username, role=UserKind(req.user.role),
                    created=req.user.created, id=req.obfuscate_int64_field(req.user.id),
                    email=req.user.email, password=None)
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
        response = ConfigurationResponse(requires_setup=(initial==initial))
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
            token = t.get_token_for_user(u.get_user(rq.username))
            resp.obj = LoginResponse(token=token)
            resp.status = '201'
        return resp


class TokenResource:

    def on_post(self, req, resp):
        u = UserController(req.session)
        t = TokenController(req.session)
        l = LoginRequest.from_json(req.body)

        if u.check_credentials(l):
            user = u.get_user(l.username)
            resp.status = '200'
            resp.obj = LoginResponse(token=t.get_or_create_token_for_user(user))
        else:
            resp.status = '403'
            resp.media = None
        return resp


class GetSessionTokenComponent:
    def process_request(self, req, resp):
        auth = req.auth
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
            return int.from_bytes(cipher.decrypt(x), byteorder='big')

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
            if resp.obj:
                logging.info(json.dumps(resp.obj.to_json()))
                resp.body = json.dumps(resp.obj.to_json())
        except AttributeError:
            pass


def create_app(engine=None):
    if not engine:
        engine = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost/annotatron", echo=True)
    Session.configure(bind=engine)
    app = falcon.API(middleware=[AttachSessionComponent(), JSONTranslatorComponent(), RequireJSONComponent(),
                                 ObfuscationComponent()])
    app.add_route("/conf/initialUser", InitialUserResource())
    return app

app = create_app()

if __name__ == '__main__':
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()