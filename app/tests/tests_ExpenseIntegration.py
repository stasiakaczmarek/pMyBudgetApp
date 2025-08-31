import os
# USTAWIENIE ZMIENNEJ ŚRODOWISKOWEJ PRZED IMPORTEM MODELI:
# W wielu aplikacjach w zależności od tej zmiennej wybierana jest inna baza np. testowa
# Dzięki temu testy nie naruszają prawdziwych danych
os.environ['TEST_MODE'] = 'True'


import unittest
from datetime import date
# Import połączenia do bazy danych i modeli używanych w testach
from database import db
from models import Expense, Category


# In-memory SQLite <=> testy integracyjne
# Faktycznie sprawdzamy, że rekord powstaje, jest modyfikowany, sumowany i usuwany w bazie
# Tworzysz, modyfikujesz i usuwasz rekordy w prawdziwej tabeli, a nie w zamockowanym obiekcie
# Sprawdzasz też agregację (category_summary) – czyli zachowanie aplikacji z realnymi danymi

class TestExpense(unittest.TestCase):
# Każdy test startuje na świeżej, in-memory bazie SQLite.

    def setUp(self):
        # Wykonywane przed każdym testem:
        # Tworzy świeżą bazę i dane startowe
        # Połącz z testową bazą SQLite w pamięci
        db.connect()
        # Utwórz tabele dla testowanych modeli
        db.create_tables([Expense, Category])

        # TC1: Tworzenie poprawnego wydatku
        # Dodajemy pojedynczy, przykładowy wydatek jako dane wyjściowe do testów
        self.test_expense = Expense.create(
            amount=100.0,
            category="Zakupy",
            date=date(2024, 5, 1)
        )

    def tearDown(self):
        # Wykonywane po każdym teście:
        # Czyści bazę i zamyka połączenie
        if not db.is_closed():
            # Usuń tabele, by kolejny test startował na czysto
            db.drop_tables([Expense, Category])
            db.close()

    # TC2: Pobieranie wszystkich wydatków
    def test_get_all_expenses(self):
        # Sprawdza, czy metoda Expense.get_all() zwraca wszystkie wydatki
        # Mamy dokładnie 1 wydatek dodany w setUp()
        expenses = Expense.get_all()
        # Powinien być 1 rekord
        self.assertEqual(len(expenses), 1)
        # Powinien mieć kwotę 100.0
        self.assertEqual(expenses[0].amount, 100.0)

    # TC3: Pobieranie wydatku po ID
    def test_get_expense_by_id(self):
        # Sprawdza pobieranie konkretnego wydatku po ID
        expense = Expense.get_by_id(self.test_expense.id)
        # Powinien istnieć
        self.assertIsNotNone(expense)
        # Kwota powinna być zgodna z setUp()
        self.assertEqual(expense.amount, 100.0)
        # Kategoria powinna być zgodna z setUp()
        self.assertEqual(expense.category, "Zakupy")

    # TC4: Pobieranie nieistniejącego wydatku
    def test_get_expense_by_id_not_found(self):
        # Sprawdza zachowanie, gdy szukamy nieistniejącego ID
        # Oczekujemy None, a nie wyjątku.
        expense = Expense.get_by_id(999999999999)
        self.assertIsNone(expense)

    # TC5: Aktualizacja wydatku
    def test_update_expense(self):
        # Sprawdza aktualizację wydatku (np. zmiana kwoty)
        # Oczekujemy, że metoda zwróci 1 (zaktualizowano 1 rekord)
        # I że zmiana jest faktycznie zapisana w bazie
        result = Expense.update_expense(self.test_expense.id, amount=150.0)
        self.assertIsInstance(result, Expense)
        self.assertEqual(result.amount, 150.0)

        # Weryfikujemy, czy kwota została zaktualizowana
        updated_expense = Expense.get_by_id(self.test_expense.id)
        self.assertEqual(updated_expense.amount, 150.0)

    # TC6: Usuwanie wydatku
    def test_delete_expense(self):
        # Sprawdza usuwanie wydatku po ID
        # Oczekujemy, że metoda zwróci 1 (usunięto 1 rekord)
        # A następnie get_by_id zwróci None
        result = Expense.delete_expense(self.test_expense.id)
        self.assertIsNone(result)

        # Weryfikujemy, czy rekord został usunięty
        self.assertIsNone(Expense.get_by_id(self.test_expense.id))


    # TC7: Pobieranie podsumowania kategorii
    def test_category_summary(self):
        # Sprawdza agregację wydatków po kategoriach (podsumowanie)
        # Dodajemy drugi wydatek w tej samej kategorii oraz jeden w innej kategprii
        # Następnie oczekujemy poprawnych sum
        # Drugi wydatek w kategorii "Zakupy"
        Expense.create(
            amount=72.0,
            category="Zakupy",
            date=date(2024, 5, 2)
        )

        # Trzeci wydatek dodajemy w innej kategorii
        Expense.create(
            amount=300.0,
            category="Biżuteria",
            date=date(2024, 5, 3)
        )

        # category_summary() powinno zwrócić listę obiektów z polami np. category i total
        summary = Expense.category_summary()
        # Mamy dwie kategorie: "Zakupy" i "Biżuteria"
        self.assertEqual(len(summary), 2)

        # Sprawdzamy, czy znajduje wpis dla "Zakupy"
        # Weryfikujemy sumę 100 + 72 = 172
        zakupy_summary = next((s for s in summary if s.category == "Zakupy"), None)
        self.assertIsNotNone(zakupy_summary)
        self.assertAlmostEqual(zakupy_summary.total, 172.0)

    # TC8: Tworzenie wydatku z ujemną kwotą
    def test_create_expense_negative_amount(self):
        with self.assertRaises(ValueError):
            Expense.create_expense(
                amount=-50.0,
                category="Zakupy",
                date=date(2024, 5, 1))

    # TC9: Tworzenie wydatku z zerową kwotą
    def test_create_expense_zero_amount(self):
        with self.assertRaises(ValueError):
            Expense.create_expense(amount=0.0,
                           category="Zakupy",
                           date=date(2024, 5, 1))

    # TC10: Aktualizacja nieistniejącego wydatku
    def test_update_nonexistent_expense(self):
        result = Expense.update_expense(999999999, amount=200.0)
        self.assertIsNone(result)

    # TC11: Usuwanie nieistniejącego wydatku
    def test_delete_nonexistent_expense(self):
        result = Expense.delete_expense(999999999)
        self.assertIsNone(result)
