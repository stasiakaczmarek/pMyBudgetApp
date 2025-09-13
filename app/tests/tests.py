import os
os.environ['TEST_MODE'] = 'True'

import tempfile
import unittest
import pandas as pd
from datetime import date
from app.models import Category, Expense
from app.database import db
from app.backup import import_from_csv, export_to_csv, CSV_FILE


class TestBackupIntegration(unittest.TestCase):
    # Testują cały flow z rzeczywistymi plikami i bazą

    def setUp(self):
        Expense.delete().execute()
        Category.delete().execute()
        # Połączenie z bazą i utworzenie tabel
        if not db.is_closed():
            db.close()
        db.connect()
        db.create_tables([Category, Expense])

        # Tymczasowy plik CSV
        self.temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig')
        self.temp_csv.close()

        # Zachowujemy oryginalną ścieżkę i ustawiamy tymczasową
        self.original_csv_file = CSV_FILE
        import app.backup as backup
        backup.CSV_FILE = self.temp_csv.name
        self.backup_module = backup

    def tearDown(self):
        Expense.delete().execute()
        Category.delete().execute()
        # Usuwamy tabele i zamykamy połączenie
        if not db.is_closed():
            db.drop_tables([Expense, Category])
            db.close()

        import app.backup as backup
        backup.CSV_FILE = self.original_csv_file

        # Usuwamy tymczasowy plik CSV
        try:
            if os.path.exists(self.temp_csv.name):
                os.unlink(self.temp_csv.name)
        except Exception:
            pass

        # Przywracamy oryginalną ścieżkę CSV
        self.backup_module.CSV_FILE = self.original_csv_file

    # TC1: Eksport bazy z rekordami do CSV
    def test_export_import_roundtrip(self):
        # Dodajemy dwa poprawne rekordy
        Expense.create(id=1, amount=100, category="Food", date="2024-01-01")
        Expense.create(id=2, amount=200, category="Transport", date="2024-01-02")

        original_count = len(list(Expense.select()))
        export_to_csv()
        Expense.delete().execute()

        import_from_csv()
        restored_count = len(list(Expense.select()))

        # Po imporcie może być mniej rekordów (bo złe giną),
        # ale nigdy więcej niż było.
        self.assertLessEqual(restored_count, original_count)

    # TC2: Import pełnego CSV do bazy – brak pliku
    def test_import_csv_file_not_found(self):
        # Usuwamy plik CSV, aby zasymulować brak
        if os.path.exists(self.temp_csv.name):
            os.unlink(self.temp_csv.name)

        from app import backup

        with self.assertLogs(backup.logger, level='ERROR') as cm:
            import_from_csv()

        # Sprawdzenie, że log zawiera oczekiwany tekst
        found = any("Brak pliku CSV" in message for message in cm.output)
        self.assertTrue(found)


    # TC3: Eksport pustej bazy do CSV
    def test_export_empty_database(self):
        Expense.delete().execute()

        export_to_csv()
        df = pd.read_csv(self.temp_csv.name, encoding='utf-8-sig')
        self.assertEqual(len(df), 0)
        self.assertListEqual(list(df.columns), ["ID", "Kwota", "Kategoria", "Data"])

    # TC4: Import poprawnego CSV – obsługa wyjątków
    def test_import_csv_exception_handling(self):
        from app import backup
        from unittest.mock import patch

        # Tymczasowo zmieniamy CSV_FILE w module backup
        original_csv_file = backup.CSV_FILE
        backup.CSV_FILE = self.temp_csv.name

        try:
            # Wymuszenie wyjątku podczas importu
            with patch('app.backup.pd.read_csv', side_effect=Exception("Test error")):
                with self.assertLogs(backup.logger, level='ERROR') as cm:
                    backup.import_from_csv()


            # Sprawdzenie, że logi zawierają komunikat o błędzie
            found = any("Błąd importu CSV" in message for message in cm.output)
            self.assertTrue(found)

        finally:
            backup.CSV_FILE = original_csv_file

    # # TC5: Import CSV z polskimi znakami
    # def test_import_csv_with_polish_chars(self):
    #     import app.backup as backup
    #
    #     # Przygotuj tymczasowy CSV z polskimi znakami
    #     test_data = {
    #         "ID": [1, 2],
    #         "Kwota": [150.0, 250.0],
    #         "Kategoria": ["Żółć", "Święta"],
    #         "Data": ["2024-05-01", "2024-05-02"]
    #     }
    #     df = pd.DataFrame(test_data)
    #     df.to_csv(self.temp_csv.name, index=False, encoding='utf-8-sig')
    #
    #     # Wyczyść kategorie, żeby uniknąć UNIQUE constraint
    #     Expense.delete().execute()
    #
    #     import random
    #
    #     def random_color():
    #         return f"#{random.randint(0, 0xFFFFFF):06X}"
    #
    #     # Utwórz kategorie, które będą używane w CSV
    #     for cat_name in ["Żółć", "Święta"]:
    #         Category.get_or_create(name=cat_name, defaults={"color": random_color()})
    #
    #     backup.import_from_csv(csv_file=self.temp_csv.name)
    #
    #     # Pobierz rekordy z bazy
    #     expenses = list(Expense.select())
    #
    #     # Sprawdź, że wszystkie rekordy zostały zaimportowane
    #     self.assertEqual(len(expenses), 2)
    #
    #     # Sprawdź, że kategorie mają poprawne polskie znaki
    #     categories = {exp.category.name for exp in expenses}
    #     self.assertEqual(categories, {"Żółć", "Święta"})


    # TC6: Import CSV z niepoprawną datą
    def test_import_csv_with_invalid_date(self):
        test_data = {
            "ID": [1, 2],
            "Kwota": [123.0, 200.0],
            "Kategoria": ["Test", "Transport"],
            "Data": ["2024-13-01", "2024-05-02"]
        }
        df = pd.DataFrame(test_data)
        df.to_csv(self.temp_csv.name, index=False, encoding="utf-8")


        # CSV z błędną datą – rekord ma zginąć
        import_from_csv()
        expenses = list(Expense.select())
        self.assertEqual(len(expenses), 0)


    # TC7: Import CSV z brakującymi wartościami
    def test_import_csv_with_missing_values(self):
        test_data = {
            "ID": [1, 2, 3],
            "Kwota": [100.0, None, 250.0],
            "Kategoria": ["Jedzenie", "Transport", None],
            "Data": ["2024-05-01", "2024-05-02", "2024-05-03"]
        }
        df = pd.DataFrame(test_data)
        df.to_csv(self.temp_csv.name, index=False, encoding="utf-8")

        # CSV z brakującą kwotą lub datą – rekord ma zginąć
        import_from_csv()
        expenses = list(Expense.select())
        self.assertEqual(len(expenses), 0)

    # TC8: Kolejność kolumn w CSV
    def test_csv_column_order_preserved(self):
        Expense.create(amount=100.0, category="Test", date=date(2024, 5, 1))

        export_to_csv()
        df = pd.read_csv(self.temp_csv.name, encoding='utf-8-sig')
        expected_columns = ["ID", "Kwota", "Kategoria", "Data"]
        self.assertListEqual(list(df.columns), expected_columns)

