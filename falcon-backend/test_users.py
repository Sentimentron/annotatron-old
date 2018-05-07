from falcon import testing
from main import create_app
from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from models import User, Token
import logging

"""
   template_engine = sa.create_engine("postgres://postgres@/postgres", echo=False)

    conn = template_engine.connect()
    conn = conn.execution_options(autocommit=False)
    conn.execute("ROLLBACK")
    try:
        conn.execute("DROP DATABASE %s" % DB_NAME)
    except sa.exc.ProgrammingError as e:
        # Could not drop the database, probably does not exist
        conn.execute("ROLLBACK")
    except sa.exc.OperationalError as e:
        # Could not drop database because it's being accessed by other users (psql prompt open?)
        conn.execute("ROLLBACK")

    conn.execute("CREATE DATABASE %s" % DB_NAME)
    conn.close()

    template_engine.dispose()
"""


class MyTestCase(testing.TestCase):

    @classmethod
    def try_drop_existing_db(cls):
        """
        Drop the existing test database, if it exists.
        :return: True on success
        """
        conn = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost:5432/postgres").connect()
        conn = conn.execution_options(autocommit=False)
        conn.execute("ROLLBACK")
        try:
            conn.execute("DROP DATABASE %s" % "annotatron_test")
        except exc.ProgrammingError as e:
            # Could not drop the database, probably does not exist
            conn.execute("ROLLBACK")
            logging.fatal("Could not drop the test database")
        except exc.OperationalError as e:
            # Could not drop database because it's being accessed by other users (psql prompt open?)
            conn.execute("ROLLBACK")
            logging.fatal("Could not drop the test database, due to concurrent access.")
            raise e
        return True

    @classmethod
    def try_create_testing_db(cls):
        """
        Copies the current Annotatron database schema to a blank new one.
        :return: An engine pointing at the new schema
        """
        conn = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost:5432/postgres",
                             isolation_level="AUTOCOMMIT").connect()
        conn = conn.execution_options(autocommit=True)
        conn.execute("CREATE DATABASE annotatron_test TEMPLATE annotatron")

        conn = create_engine("postgresql+psycopg2://annotatron:annotatron@localhost:5432/annotatron_test",
                             isolation_level="AUTOCOMMIT")
        return conn

    def setUp(self):
        super(MyTestCase, self).setUp()

        self.try_drop_existing_db()
        self.engine = self.try_create_testing_db()

        self.connection = self.engine.connect()

        # begin a non-ORM transaction
        self.trans = self.connection.begin()
        Session = sessionmaker()
        self.session = Session(bind=self.connection)

        self.app = create_app(self.connection)
        self.session.query(Token).delete()
        self.session.query(User).delete()
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.trans.rollback()
        self.connection.close()


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
        print(result.json)

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

        self.assertEqual(current, result.json["token"])


