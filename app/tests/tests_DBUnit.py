# import unittest
# from unittest.mock import patch, MagicMock
# import app.database as database
# from app import models
#
#
# class TestDatabaseUnit(unittest.TestCase):
#
#     @patch('app.database.db')
#     def test_init_db_calls_connect_and_create_tables(self, mock_db):
#         # db.is_closed zwraca True, więc init_db powinno wywołać connect i create_tables
#         mock_db.is_closed.return_value = True
#         # Mockujemy BaseModel.__subclasses__
#         mock_base_model = MagicMock()
#         with patch('app.models.BaseModel.__subclasses__', return_value=[mock_base_model]):
#             database.init_db()
#
#         mock_db.connect.assert_called_once()
#         mock_db.create_tables.assert_called_once_with([mock_base_model], safe=True)
#
#     @patch('app.database.db')
#     def test_init_db_when_already_connected(self, mock_db):
#         # db.is_closed zwraca False → connect nie powinno być wywołane
#         mock_db.is_closed.return_value = False
#         with patch('app.database.BaseModel.__subclasses__', return_value=[]):
#             database.init_db()
#
#         mock_db.connect.assert_not_called()
#         mock_db.create_tables.assert_called_once_with([], safe=True)
#
#     @patch('app.database.db')
#     def test_close_db_calls_close(self, mock_db):
#         mock_db.is_closed.return_value = False
#         database.close_db()
#         mock_db.close.assert_called_once()
#
#     @patch('app.database.db')
#     def test_close_db_when_already_closed(self, mock_db):
#         mock_db.is_closed.return_value = True
#         database.close_db()
#         mock_db.close.assert_not_called()
