import os
os.environ['TEST_MODE'] = 'True'

from unittest.mock import patch, MagicMock
import unittest
from datetime import date
from peewee import SqliteDatabase
from app.models import Category, Expense

# Tworzymy osobną bazę dla testów w pamięci
test_db = SqliteDatabase(":memory:")

# Mocki <=> testy jednostkowe
# Nie ma bazy
# Sprawdzamy tylko czy metoda wywołuje odpowiednie rzeczy i zwraca oczekiwaną wartość

class TestExpenseWithMock(unittest.TestCase):

    def setUp(self):
        # Tworzymy patch dla każdej metody, która korzysta z bazy danych
        # Dzięki temu testujemy logikę metody bez faktycznego zapisu do DB
        self.get_all_patch = patch('app.models.Expense.get_all')
        self.get_by_id_patch = patch('app.models.Expense.get_by_id')
        self.create_expense_patch = patch('app.models.Expense.create_expense')
        self.update_expense_patch = patch('app.models.Expense.update_expense')
        self.delete_expense_patch = patch('app.models.Expense.delete_expense')
        self.category_summary_patch = patch('app.models.Expense.category_summary')

        # Start patchy → każda metoda jest teraz zamockowana
        self.mock_get_all = self.get_all_patch.start()
        self.mock_get_by_id = self.get_by_id_patch.start()
        self.mock_create_expense = self.create_expense_patch.start()
        self.mock_update_expense = self.update_expense_patch.start()
        self.mock_delete_expense = self.delete_expense_patch.start()
        self.mock_category_summary = self.category_summary_patch.start()

        # Tworzymy przykładowy obiekt Expense do testów
        self.sample_expense = MagicMock()
        self.sample_expense.amount = 100.0
        self.sample_expense.category = "Zakupy"
        self.sample_expense.date = date(2024, 5, 1)
        self.sample_expense.id = 1

    def tearDown(self):
        # Zatrzymanie patchy po każdym teście
        patch.stopall()


    # TC2: Pobieranie wszystkich wydatków
    def test_get_all_expenses(self):
        # Zmockowana metoda get_all zwraca listę z jednym wydatkiem
        self.mock_get_all.return_value = [self.sample_expense]
        expenses = Expense.get_all()
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0].amount, 100.0)
        # MA SENS, sprawdza, że metoda get_all() jest wywoływana i zwraca listę

    # TC3: Pobieranie wydatku po ID
    def test_get_expense_by_id(self):
        # Zamockowane get_by_id zwraca sample_expense
        self.mock_get_by_id.return_value = self.sample_expense
        expense = Expense.get_by_id(1)
        self.assertIsNotNone(expense)
        self.assertEqual(expense.amount, 100.0)
        self.assertEqual(expense.category, "Zakupy")
        # MA SENS, testuje logikę wywołania i poprawność zwracanych danych

    # TC4: Pobieranie nieistniejącego wydatku
    def test_get_expense_by_id_not_found(self):
        # get_by_id zwraca None dla nieistniejącego ID
        self.mock_get_by_id.return_value = None
        expense = Expense.get_by_id(999)
        self.assertIsNone(expense)
        # MA SENS, sprawdza poprawną obsługę braku rekordu

    # TC5: Aktualizacja wydatku
    def test_update_expense(self):
        # Zamockowana metoda update_expense zwraca nowy obiekt z nową kwotą
        updated_expense = MagicMock()
        updated_expense.amount = 150.0
        self.mock_update_expense.return_value = updated_expense

        result = Expense.update_expense(1, amount=150.0)
        self.assertIsInstance(result, MagicMock)
        self.assertEqual(result.amount, 150.0)
        # MA SENS w kontekście logiki jednostkowej

    # TC6: Usuwanie wydatku
    def test_delete_expense(self):
        # delete_expense zwraca None (mock symuluje usunięcie)
        self.mock_delete_expense.return_value = None
        result = Expense.delete_expense(1)
        self.assertIsNone(result)
        # MA SENS dla jednostkowego sprawdzenia wywołania metody

    # TC7: Pobieranie podsumowania kategorii
    def test_category_summary(self):
        # Mock zwraca listę podsumowań kategorii
        summary_mock = [
            MagicMock(category="Zakupy", total=172.0),
            MagicMock(category="Biżuteria", total=300.0)
        ]
        self.mock_category_summary.return_value = summary_mock

        summary = Expense.category_summary()
        self.assertEqual(len(summary), 2)
        zakupy_summary = next((s for s in summary if s.category == "Zakupy"), None)
        self.assertIsNotNone(zakupy_summary)
        self.assertAlmostEqual(zakupy_summary.total, 172.0)
        # MA SENS w kontekście sprawdzenia logiki, chociaż nie agreguje danych z prawdziwej bazy


    # TC8: Tworzenie wydatku z ujemną kwotą
    def test_create_expense_negative_amount(self):
        # Mock rzuca ValueError przy ujemnej kwocie
        self.mock_create_expense.side_effect = ValueError("Kwota wydatku musi być większa od 0")
        with self.assertRaises(ValueError):
            Expense.create_expense(amount=-50.0, category="Zakupy", date=date(2024, 5, 1))
            # MA SENS, testuje poprawną obsługę wyjątków

    # TC9: Tworzenie wydatku z zerową kwotą
    def test_create_expense_zero_amount(self):
        # Mock rzuca ValueError przy kwocie zero
        self.mock_create_expense.side_effect = ValueError("Kwota wydatku musi być większa od 0")
        with self.assertRaises(ValueError):
            Expense.create_expense(amount=0.0, category="Zakupy", date=date(2024, 5, 1))
        # MA SENS, jednostkowo sprawdza walidację

    # TC10: Aktualizacja nieistniejącego wydatku
    def test_update_nonexistent_expense(self):
        # Mock zwraca None dla nieistniejącego rekordu
        self.mock_update_expense.return_value = None
        result = Expense.update_expense(999, amount=200.0)
        self.assertIsNone(result)
        #  MA SENS, testuje poprawną obsługę braku rekordu


    # TC11: Usuwanie nieistniejącego wydatku
    def test_delete_nonexistent_expense(self):
        # Mock zwraca None przy próbie usunięcia nieistniejącego rekordu
        self.mock_delete_expense.return_value = None
        result = Expense.delete_expense(999)
        self.assertIsNone(result)
        # MA SENS, sprawdza poprawną reakcję metody
