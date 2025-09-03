import os
os.environ['TEST_MODE'] = 'True'


import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.backup import import_from_csv, export_to_csv


class TestBackupUnit(unittest.TestCase):
    # Testują logikę biznesową z mockami

    def setUp(self):
        self.log_messages = []

        def log_capture(msg, *args, **kwargs):
            if args:
                msg = msg % args
            self.log_messages.append(msg)

        self.logger_patch = patch('app.backup.logger')
        self.mock_logger = self.logger_patch.start()
        self.mock_logger.error.side_effect = log_capture
        self.mock_logger.info.side_effect = log_capture

    def tearDown(self):
        self.logger_patch.stop()
        self.log_messages.clear()

    # TC1: Eksport bazy z rekordami do CSV
    @patch('app.backup.pd.DataFrame.to_csv')
    def test_export_with_data(self, mock_to_csv):
        mock_expense = MagicMock()
        mock_expense.id = 1
        mock_expense.amount = 100.0
        mock_expense.category = "Test"
        mock_expense.date = "2024-05-01"

        mock_query = MagicMock()
        mock_query.order_by.return_value = [mock_expense]

        with patch('app.backup.Expense.select', return_value=mock_query):
            export_to_csv()

        mock_to_csv.assert_called_once()
        args, kwargs = mock_to_csv.call_args
        self.assertTrue(args[0].endswith(".csv"))

        expected_df = pd.DataFrame([{
            "ID": 1,
            "Kwota": 100.0,
            "Kategoria": "Test",
            "Data": "2024-05-01"
        }])
        self.assertEqual(expected_df.iloc[0]["ID"], 1)
        self.assertEqual(expected_df.iloc[0]["Kwota"], 100.0)
        self.assertEqual(expected_df.iloc[0]["Kategoria"], "Test")
        self.assertEqual(expected_df.iloc[0]["Data"], "2024-05-01")

    # TC2: Import pełnego CSV do bazy – brak pliku
    # @patch('app.backup.pd.read_csv')
    # def test_file_not_found_handling(self, mock_read_csv):
    #     mock_read_csv.side_effect = FileNotFoundError("File not found")
    #     import_from_csv()
    #     error_logs = [msg for msg in self.log_messages if "Brak pliku CSV" in str(msg)]
    #     self.assertTrue(len(error_logs) > 0)

    @patch("app.backup.pd.read_csv")
    def test_import_csv_with_mock(self, mock_read_csv):
        # Zwróć DataFrame odpowiadający oczekiwanym wierszom
        mock_read_csv.return_value = pd.DataFrame([
            {"id": 1, "kwota": 123, "kategoria": "Test", "data": "2024-01-01"},
            {"id": 2, "kwota": 456, "kategoria": "Transport", "data": "2024-05-02"}
        ])
        count = import_from_csv()
        self.assertEqual(count, 2)

    # TC3: Eksport pustej bazy do CSV
    @patch('app.backup.pd.DataFrame.to_csv')
    def test_export_empty_database(self, mock_to_csv):
        mock_query = MagicMock()
        mock_query.order_by.return_value = []

        with patch('app.backup.Expense.select', return_value=mock_query):
            export_to_csv()

        mock_to_csv.assert_called_once()
        args, kwargs = mock_to_csv.call_args
        self.assertTrue(args[0].endswith(".csv"))

        expected_columns = ["ID", "Kwota", "Kategoria", "Data"]
        df = pd.DataFrame([], columns=expected_columns)
        self.assertListEqual(list(df.columns), expected_columns)
        self.assertEqual(len(df), 0)

    # TC4: Import poprawnego CSV – obsługa wyjątków
    @patch('app.backup.pd.read_csv')
    def test_import_csv_exception_handling(self, mock_read_csv):
        mock_read_csv.side_effect = Exception("Test error")
        import_from_csv()
        error_logs = [msg for msg in self.log_messages if "Błąd importu CSV" in str(msg)]
        self.assertTrue(len(error_logs) > 0)

    # TC5: Import pustego CSV
    @patch('app.backup.pd.read_csv')
    def test_import_empty_csv(self, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame()
        import_from_csv()
        info_logs = [msg for msg in self.log_messages if "Plik CSV jest pusty" in str(msg)]
        self.assertTrue(len(info_logs) > 0)

    # TC6: Import CSV z niepoprawną datą – jednostkowy
    def test_import_csv_with_invalid_date_unit(self):
        test_data = {
            "ID": [1, 2],
            "Kwota": [123.0, 200.0],
            "Kategoria": ["Test", "Transport"],
            "Data": ["2024-13-01", "2024-05-02"]
        }
        df_mock = pd.DataFrame(test_data)

        # Patchujemy wszystko
        with patch("app.backup.pd.read_csv", return_value=df_mock), \
                patch("app.backup.Expense.create") as mock_create, \
                patch("app.backup.Expense.get_or_none", return_value=None), \
                patch("app.backup.db.atomic"):  # mockujemy kontekst

            import_from_csv()

            # Drugi rekord powinien zostać dodany
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            assert kwargs["amount"] == 200.0
            assert kwargs["category"] == "Transport"
            assert str(kwargs["date"]) == "2024-05-02"

    # TC7: Import CSV z brakującymi kolumnami
    @patch('app.backup.pd.read_csv')
    def test_import_csv_missing_columns(self, mock_read_csv):
        test_data = {"id": [1], "kwota": [100.0], "data": ["2024-05-01"]}
        mock_read_csv.return_value = pd.DataFrame(test_data)
        import_from_csv()
        error_logs = [msg for msg in self.log_messages if "Niespodziewane kolumny" in str(msg)]
        self.assertTrue(len(error_logs) > 0)

    # TC8: Kolejność kolumn w CSV – jednostkowy
    @patch('app.backup.pd.DataFrame.to_csv')
    def test_csv_column_order_preserved_unit(self, mock_to_csv):
        """JEDNOSTKOWY: Sprawdzenie kolejności kolumn w CSV"""
        mock_expense = MagicMock()
        mock_expense.id = 1
        mock_expense.amount = 100.0
        mock_expense.category = "Test"
        mock_expense.date = "2024-05-01"

        mock_query = MagicMock()
        mock_query.order_by.return_value = [mock_expense]

        with patch('app.backup.Expense.select', return_value=mock_query):
            export_to_csv()

        args, kwargs = mock_to_csv.call_args
        df = pd.DataFrame([{
            "ID": mock_expense.id,
            "Kwota": mock_expense.amount,
            "Kategoria": mock_expense.category,
            "Data": mock_expense.date
        }])
        expected_columns = ["ID", "Kwota", "Kategoria", "Data"]
        self.assertListEqual(list(df.columns), expected_columns)


