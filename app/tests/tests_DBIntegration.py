from peewee import Model, CharField
from app.database import db, init_db, close_db
import unittest

class DummyModel(Model):
    name = CharField()
    class Meta:
        database = db

class TestDatabaseIntegration(unittest.TestCase):
    def setUp(self):
        init_db()
        db.create_tables([DummyModel], safe=True)

    def tearDown(self):
        db.drop_tables([DummyModel], safe=True)
        close_db()

    def test_init_db_creates_tables(self):
        tables = db.get_tables()
        self.assertIn('dummymodel', tables)
