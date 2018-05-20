from falcon import testing
import falcon
from main import create_app
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from models import InternalUser, InternalToken
import logging
import gc
import os
import random
import string
import sys

from pyannotatron.models import AnnotatronUser, UserKind, NewUserRequest, LoginResponse, LoginRequest


class MyTestCase(testing.TestCase):

    def try_drop_existing_db(self):
        """
        Drop the existing test database, if it exists.
        :return: True on success
        """
        conn = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost:5432/postgres").connect()
        conn = conn.execution_options(autocommit=False)
        conn.execute("ROLLBACK")
        try:
            conn.execute("DROP DATABASE %s" % self.db_name)
        except exc.ProgrammingError as e:
            # Could not drop the database, probably does not exist
            conn.execute("ROLLBACK")
            logging.error("Could not drop the test database: %s", e)
        except exc.OperationalError as e:
            # Could not drop database because it's being accessed by other users (psql prompt open?)
            conn.execute("ROLLBACK")
            logging.fatal("Could not drop the test database, due to concurrent access.")
            raise e
        return True

    @classmethod
    def generate_db_name(cls):
        database_suffix = ''.join(random.sample(string.ascii_lowercase, 8))
        return "annotatron_test_{}".format(database_suffix)

    def try_create_testing_db(self):
        """
        Copies the current Annotatron database schema to a blank new one.
        :return: An engine pointing at the new schema
        """

        gc.collect()
        # Create the testing database
        conn = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost:5432/postgres",
                             isolation_level="AUTOCOMMIT").connect()

        self.db_name = self.generate_db_name()
        logging.info("Creating database %s...", self.db_name)

        conn.execute("CREATE DATABASE {}".format(self.db_name))
        conn.close()

        # Read the Annotatron SQL specification
        current_directory = os.path.dirname(os.path.realpath(__file__))
        docker_db_file = os.path.join(current_directory, "../docker/postgres/files/db.sql")
        with open(docker_db_file, "r") as fin:
            database_statements = fin.read()

        # Create the database tables with an up-to-date schema
        conn = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost:5432/{}".format(self.db_name),
                             isolation_level="AUTOCOMMIT")
        conn.execute(database_statements)
        conn.dispose()

        # Create a connection with the default isolation level
        conn = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost:5432/{}".format(self.db_name))
        return conn

    def setUp(self):
        super(MyTestCase, self).setUp()

        self.db_name = None

        self.engine = self.try_create_testing_db()

        self.connection = self.engine.connect()

        # begin a non-ORM transaction
        self.trans = self.connection.begin()
        Session = sessionmaker()
        self.session = Session(bind=self.connection)

        self.app = create_app(self.connection)
        self.session.query(InternalToken).delete()
        self.session.query(InternalUser).delete()
        self.session.commit()


    def tearDown(self):
        self.app = None
        self.session.close()
        self.trans.rollback()
        self.connection.close()
        self.engine.dispose()

        # From https://stackoverflow.com/questions/4414234/getting-pythons-unittest-results-in-a-teardown-method/39606065#39606065
        if hasattr(self, '_outcome'):  # Python 3.4+
            result = self.defaultTestResult()  # these 2 methods have no side effects
            self._feedErrorsToResult(result, self._outcome.errors)
        else:  # Python 3.2 - 3.3 or 3.0 - 3.1 and 2.7
            result = getattr(self, '_outcomeForDoCleanups', self._resultForDoCleanups)
        error = result.errors
        failure = result.failures
        ok = not error and not failure

        gc.collect()

        if not ok:
            logging.error("Failing database at %s", self.db_name)
        else:
            self.try_drop_existing_db()


class TestCaseWithDefaultAdmin(MyTestCase):
    def setUp(self):
        super().setUp()
        self.current_token = None
        initial_user = {
            "username": "admin",
            "email": "admin@test.com",
            "password": "Faaar",
            "role": "Administrator"
        }

        result = self.simulate_post('/conf/initialUser', json=initial_user)

        self.assertTrue("token" in result.json)
        self.current_token = result.json["token"]

    def simulate_request(self, *args, **kwargs):
        headers = {}
        #kwargs["auth"] = "Bearer {}".format(self.current_token)
        if True:
            if "auth" in kwargs:
                headers = kwargs["headers"]
            if self.current_token:
                headers["Authorization"] = "Bearer {}".format(self.current_token)
        kwargs["headers"] = headers
        return super().simulate_request(*args, **kwargs)

    def get_current_user_id(self):
        response = self.simulate_get("/auth/whoAmI")
        self.assertEqual(response.status_code, 302)
        location = response.headers["location"]
        return location.split('/')[-1]


class TestCaseOnlyWithDefaultAdmin(TestCaseWithDefaultAdmin):

    def test_whoami(self):
        response = self.simulate_get("/auth/whoAmI")
        self.assertEqual(response.status_code, 302)
        location = response.headers["location"]

        response = self.simulate_get(location)
        u = AnnotatronUser.from_json(response.json)
        self.assertEqual(u.username, "admin")
        self.assertEqual(u.email, "admin@test.com")
        self.assertEqual(u.role, UserKind.ADMINISTRATOR)

    def test_password_self_change(self):
        """
            TODO: check that Administrators can change user account passwords.
                    LoginResponse should indicate password reset bit.
            TODO: check that Administrators can change other Administrator's passwords (so long as there's
                  always one Administrator who doesn't require a password reset.)
            TODO: check that Staff/Annotator/Reviewer users can change their own passwords.
            TODO: check that Staff/Annotator/Reviewer users can't change other people's passwords.
        """

        old_token = self.current_token
        current_id = self.get_current_user_id()
        password_change = {
            "oldPassword": "Faaar",
            "newPassword": "Blarg"
        }

        response = self.simulate_put("/auth/users/{}/password".format(current_id), json=password_change)
        self.assertEqual(response.status, falcon.HTTP_202)

        login_request = {
            "username": "admin",
            "password": "Blarg"
        }
        response = self.simulate_post("/auth/token", json=login_request)
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.assertTrue("token" in response.json)
        self.current_token = response.json["token"]

        self.assertNotEqual(self.current_token, old_token)

        new_id = self.get_current_user_id()
        self.assertEqual(new_id, current_id)

    def test_password_self_change_with_wrong_password(self):
        current_id = self.get_current_user_id()
        password_change = {
            "oldPassword": "Faaara",
            "newPassword": "Blarg"
        }

        response = self.simulate_put("/auth/users/{}/password".format(current_id), json=password_change)
        self.assertEqual(response.status, falcon.HTTP_FORBIDDEN)

    def test_can_create_users(self):
        n = NewUserRequest("staff", "staff@ant.io", UserKind.STAFF, "kerflaag")
        response = self.simulate_post("/auth/users", json=n.to_json())
        self.assertEqual(response.status, falcon.HTTP_201)

        login_request = LoginRequest("staff", "kerflaag")
        response = self.simulate_post("/auth/token", json=login_request.to_json())
        self.assertEqual(response.status, falcon.HTTP_200)
        login_response = LoginResponse.from_json(response.json)

        self.assertTrue(login_response.password_reset_needed)


class TestCaseWithEachUserType(TestCaseWithDefaultAdmin):

    def setUp(self):
        super().setUp()
        n = NewUserRequest("staff", "staff@ant.io", UserKind.STAFF, "kerflaag")
        response = self.simulate_post("/auth/users", json=n.to_json())
        self.assertEqual(response.status, falcon.HTTP_201)

        n = NewUserRequest("reviewer", "reviewer@ant.io", UserKind.REVIEWER, "kerflaag")
        response = self.simulate_post("/auth/users", json=n.to_json())
        self.assertEqual(response.status, falcon.HTTP_201)

        n = NewUserRequest("annotator", "reviewer@ant.io", UserKind.ANNOTATOR, "kerflaag")
        response = self.simulate_post("/auth/users", json=n.to_json())
        self.assertEqual(response.status, falcon.HTTP_201)

        # Retrieve a list of users
        response = self.simulate_get("/auth/users")
        self.assertEqual(response.status, falcon.HTTP_OK)
        self.user_map = {}
        for user_id in response.json:
            response = self.simulate_get("/auth/users/{}".format(user_id))
            active_user = AnnotatronUser.from_json(response.json)
            self.user_map[user_id] = active_user

class TestPasswordSecurity(TestCaseWithEachUserType):

    def switch_to_user_role(self, role: UserKind):
        for user_id in self.user_map:
            if self.user_map[user_id].role == role:
                active_user = self.user_map[user_id]
        login_request = LoginRequest(active_user.username, "kerflaag")
        response = self.simulate_post("/auth/token", json=login_request.to_json())
        self.assertEqual(response.status, falcon.HTTP_200)
        login_response = LoginResponse.from_json(response.json)
        self.current_token = login_response.token
        return login_response

    def test_admin_can_reset_user_password(self):
        current_id = [x for x in self.user_map if self.user_map[x].role != UserKind.ADMINISTRATOR][0]
        password_change = {
            "newPassword": "Blarg"
        }

        response = self.simulate_put("/auth/users/{}/password".format(current_id), json=password_change)
        self.assertEqual(response.status, falcon.HTTP_202)

        current_user = self.user_map[current_id]
        login_request = LoginRequest(current_user.username, "Blarg")
        response = self.simulate_post("/auth/token", json=login_request.to_json())
        login_response = LoginResponse.from_json(response.json)
        self.assertTrue(login_response.password_reset_needed)

    def test_user_can_set_own_password(self):
        current_id = [x for x in self.user_map if self.user_map[x].role != UserKind.ADMINISTRATOR][0]
        password_change = {
            "oldPassword": "kerflaag",
            "newPassword": "Blarg"
        }

        current_user = self.user_map[current_id]
        self.switch_to_user_role(current_user.role)

        response = self.simulate_put("/auth/users/{}/password".format(current_id), json=password_change)
        self.assertEqual(response.status, falcon.HTTP_202)

        current_user = self.user_map[current_id]
        login_request = LoginRequest(current_user.username, "Blarg")
        response = self.simulate_post("/auth/token", json=login_request.to_json())
        login_response = LoginResponse.from_json(response.json)
        self.assertFalse(login_response.password_reset_needed)


class TestInitialUserResources(MyTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        self.session.rollback()

    def test_initial_flow(self):
        result = self.simulate_get('/conf/initialUser')
        expected = {
            "requiresSetup": True
        }
        self.assertDictEqual(result.json, expected)

        initial_user = {
            "username": "admin",
            "email": "admin@test.com",
            "password": "Faaar",
            "role": "Administrator"
        }

        result = self.simulate_post('/conf/initialUser', json=initial_user)

        self.assertTrue("token" in result.json)
        current = result.json["token"]

        result = self.simulate_get('/conf/initialUser')
        expected = {
            "requiresSetup": False
        }
        self.assertDictEqual(result.json, expected)

        new_user = {
            "username": "admin",
            "password": "Faaar"
        }

        result = self.simulate_post('/auth/token', json=new_user)
        self.assertTrue("token" in result.json)
        self.assertTrue("passwordResetNeeded" in result.json)
        self.assertFalse(result.json["passwordResetNeeded"])

        self.assertEqual(current, result.json["token"])


