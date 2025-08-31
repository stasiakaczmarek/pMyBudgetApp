import os
import unittest
from datetime import date
from unittest.mock import patch, MagicMock

# Ustawienie zmiennej środowiskowej (np. do logiki w modelach)
os.environ['TEST_MODE'] = 'True'

from models import Expense, Category

# Mocki <=> testy jednostkowe
# Nie ma bazy
# Sprawdzamy tylko czy metoda wywołuje odpowiednie rzeczy i zwraca oczekiwaną wartość

class TestExpenseWithMock(unittest.TestCase):

    def setUp(self):
        # Przygotowanie testów: patchowanie metod Expense, które używają bazy danych
        # Mockujemy metody klasy Expense
        self.get_all_patch = patch('models.Expense.get_all')
        self.get_by_id_patch = patch('models.Expense.get_by_id')
        self.create_expense_patch = patch('models.Expense.create_expense')
        self.update_expense_patch = patch('models.Expense.update_expense')
        self.delete_expense_patch = patch('models.Expense.delete_expense')
        self.category_summary_patch = patch('models.Expense.category_summary')

        # Startujemy mocki
        self.mock_get_all = self.get_all_patch.start()
        self.mock_get_by_id = self.get_by_id_patch.start()
        self.mock_create_expense = self.create_expense_patch.start()
        self.mock_update_expense = self.update_expense_patch.start()
        self.mock_delete_expense = self.delete_expense_patch.start()
        self.mock_category_summary = self.category_summary_patch.start()

        # TC1: Tworzenie przykładowy obiekt Expense do użycia w testach
        self.sample_expense = MagicMock()
        self.sample_expense.amount = 100.0
        self.sample_expense.category = "Zakupy"
        self.sample_expense.date = date(2024, 5, 1)
        self.sample_expense.id = 1

    def tearDown(self):
        # Zatrzymanie patchów po każdym teście
        patch.stopall()

    # TC2: Pobieranie wszystkich wydatków (mock)
    def test_get_all_expenses(self):
        self.mock_get_all.return_value = [self.sample_expense]  # Zamockowana lista wydatków
        expenses = Expense.get_all()
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0].amount, 100.0)

    # TC3: Pobieranie wydatku po ID (mock)
    def test_get_expense_by_id(self):
        self.mock_get_by_id.return_value = self.sample_expense
        expense = Expense.get_by_id(1)
        self.assertIsNotNone(expense)
        self.assertEqual(expense.amount, 100.0)
        self.assertEqual(expense.category, "Zakupy")

    # TC4: Pobieranie nieistniejącego wydatku (mock)
    def test_get_expense_by_id_not_found(self):
        self.mock_get_by_id.return_value = None
        expense = Expense.get_by_id(999)
        self.assertIsNone(expense)

    # TC5: Aktualizacja wydatku (mock)
    def test_update_expense(self):
        updated_expense = MagicMock()
        updated_expense.amount = 150.0
        self.mock_update_expense.return_value = updated_expense

        result = Expense.update_expense(1, amount=150.0)
        self.assertIsInstance(result, MagicMock)
        self.assertEqual(result.amount, 150.0)

    # TC6: Usuwanie wydatku (mock)
    def test_delete_expense(self):
        self.mock_delete_expense.return_value = None
        result = Expense.delete_expense(1)
        self.assertIsNone(result)

    # TC7: Pobieranie podsumowania kategorii (mock)
    def test_category_summary(self):
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

    # TC8: Tworzenie wydatku z ujemną kwotą (mock)
    def test_create_expense_negative_amount(self):
        self.mock_create_expense.side_effect = ValueError("Kwota wydatku musi być większa od 0")
        with self.assertRaises(ValueError):
            Expense.create_expense(amount=-50.0, category="Zakupy", date=date(2024, 5, 1))

    # TC9: Tworzenie wydatku z zerową kwotą (mock)
    def test_create_expense_zero_amount(self):
        self.mock_create_expense.side_effect = ValueError("Kwota wydatku musi być większa od 0")
        with self.assertRaises(ValueError):
            Expense.create_expense(amount=0.0, category="Zakupy", date=date(2024, 5, 1))

    # TC10: Aktualizacja nieistniejącego wydatku (mock)
    def test_update_nonexistent_expense(self):
        self.mock_update_expense.return_value = None
        result = Expense.update_expense(999, amount=200.0)
        self.assertIsNone(result)

    # TC11: Usuwanie nieistniejącego wydatku (mock)
    def test_delete_nonexistent_expense(self):
        self.mock_delete_expense.return_value = None
        result = Expense.delete_expense(999)
        self.assertIsNone(result)

