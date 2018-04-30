import falcon
from pyannotatron.models import ConfigurationResponse, NewUserRequest, ValidationError, FieldError

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Binary, Enum
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from wsgiref import simple_server
import json
import logging
import bcrypt


Base = declarative_base()
Session = sessionmaker()

class User(Base):
    __tablename__ = "an_users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    created = Column(DateTime)
    email = Column(String)
    password = Column(Binary)
    random_seed = Column(Binary)
    password_last_changed = Column(DateTime)
    role = Column(Enum("Administrator", "Staff", "Reviewer", "Annotator"))
    deactivated_on = Column(DateTime)


class UserController:

    def __init__(self, storage):
        self.storage = storage

    def get_administrators(self):
        return self.storage.query(User).filter_by(role='Administrator')

    def initial_user_created(self) -> bool:
        return self.get_administrators().count() > 0

    def _create_password_hash(self, seed, password):


    def _create_user(self, rq: NewUserRequest) -> ValidationError:
        # Check for obvious issues like missing fields
        errors = rq.check_for_problems()
        if len(errors) > 0:
            return errors

        # Encrypt, salt user password
        password_hash = bcrypt.hashpw(rq.password, bcrypt.gensalt())

        u = User(
            username = rq.username,
            role = rq.role,
            password = password_hash
        )

        self.storage.add(u)
        return None

    def create_initial_user(self, rq) -> ValidationError:
        if self.initial_user_created():
            return [FieldError("_state", "initial user already created")]

        rq.role = "Administrator"
        return self._create_user(rq)


class InitialUserResource:

    def on_get(self, req, resp): # checkNeedsSetup
        initial = not UserController(req.session).initial_user_created()
        response = ConfigurationResponse(requires_setup=(initial==initial))
        resp.content = response
        print(response)
        print(response.to_json())
        resp.media = response
        resp.status = falcon.HTTP_200
        return resp

    def on_post(self, req, resp):
        u = UserController(req.session)
        errors = u.create_initial_user(NewUserRequest.from_json(req.body))
        if errors:
            resp.media = errors
            resp.status = falcon.HTTPNotAcceptable
        else:
            resp.media = None
            resp.status = '201'


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
            req.context['doc'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        logging.info(json.dumps(resp.media.to_json()))
        resp.body = json.dumps(resp.media.to_json())


app = falcon.API(middleware=[AttachSessionComponent(), JSONTranslatorComponent()])
engine = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost/annotatron", echo=True)
Session.configure(bind=engine)
app.add_route("/conf/initialUser", InitialUserResource())

if __name__ == '__main__':
    httpd = simple_server.make_server('127.0.0.1', 8000, app)
    httpd.serve_forever()