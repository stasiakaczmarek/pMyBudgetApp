import os
# USTAWIENIE ZMIENNEJ ŚRODOWISKOWEJ PRZED IMPORTEM MODELI:
# W wielu aplikacjach w zależności od tej zmiennej wybierana jest inna baza (np. testowa)
# Dzięki temu testy nie naruszają "prawdziwych" danych
os.environ['TEST_MODE'] = 'True'

from datetime import date
# Import połączenia do bazy danych i modeli używanych w testach
import unittest
from database import db
from models import Expense, Category



class TestCategory(unittest.TestCase):
# Zestaw testów jednostkowych dla modelu Category (Kategoria)

    def setUp(self):
        # Przygotowanie bazy i danych przed każdym testem kategorii
        db.connect()
        db.create_tables([Category])
        # Bazowa kategoria do testów pobierania i usuwania
        self.test_category = Category.create(name="TestCategory")

    def tearDown(self):
        # Sprzątanie po każdym teście kategorii
        if not db.is_closed():
            db.drop_tables([Category])
            db.close()

    def test_create_category(self):
        # Sprawdza, czy można utworzyć nową kategorię przy pomocy metody pomocniczej
        category = Category.create_category("NewCategory")
        self.assertIsNotNone(category)
        self.assertEqual(category.name, "NewCategory")

    def test_get_all_categories(self):
        # Sprawdza, czy pobieranie wszystkich kategorii zwraca tylko tę z setUp()
        categories = Category.get_all_categories()
        # Powinien być 1 rekord
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, "TestCategory")

    def test_delete_by_name(self):
        # Sprawdza usuwanie kategorii po nazwie
        # Oczekujemy wartości 1 (usunięto jeden rekord), a potem brak kategorii
        result = Category.delete_by_name("TestCategory")
        self.assertEqual(result, 1)

        categories = Category.get_all_categories()
        self.assertEqual(len(categories), 0)

