import os
os.environ['TEST_MODE'] = 'True'

import unittest
from models import Category, Expense
from database import db
from colors import PASTEL_COLORS


class TestCategory(unittest.TestCase):
    # Każdy test startuje na świeżej, in-memory bazie SQLite.

    def setUp(self):
        # Wykonywane przed każdym testem:
        # Tworzy świeżą bazę i dane startowe
        # Połącz z testową bazą SQLite w pamięci
        db.connect()
        # Utwórz tabele dla testowanych modeli
        db.create_tables([Expense, Category])

    def tearDown(self):
        # Wykonywane po każdym teście:
        # Czyści bazę i zamyka połączenie
        if not db.is_closed():
            # Usuń tabele, by kolejny test startował na czysto
            db.drop_tables([Expense, Category])
            db.close()

    # TC1: Tworzenie kategorii z kolorem zdefiniowanym w PASTEL_COLORS
    def test_create_category_with_preset_color(self):
        name = "Buty"
        cat = Category.create_category(name, color=None)
        self.assertEqual(cat.name, name)
        self.assertEqual(cat.color, PASTEL_COLORS[name])
        self.assertTrue(cat.is_active)

    # TC2: Tworzenie kategorii z losowym kolorem (nie w PASTEL_COLORS)
    def test_create_category_with_random_color(self):
        name = "X"
        cat = Category.create_category(name, color=None)
        self.assertEqual(cat.name, name)
        self.assertTrue(cat.color.startswith("#"))
        self.assertTrue(cat.is_active)

    # TC3: Pobieranie wszystkich kategorii
    def test_get_all_categories(self):
        Category.create_category("X", color=None)
        Category.create_category("Y", color=None)
        cats = Category.get_all_categories()
        self.assertEqual(len(cats), 2)
        self.assertListEqual(sorted([c.name for c in cats]), ["X", "Y"])


    def test_get_active_categories(self):
        # TC4: Pobieranie tylko aktywnych kategorii
        # Tworzymy dwie kategorie: jedna aktywna, druga dezaktywowana
        cat1 = Category.create_category("Aktywna", color=None)
        cat2 = Category.create_category("Nieaktywna", color=None)
        Category.deactivate_category("Nieaktywna")

        # Pobieramy tylko aktywne kategorie
        active_cats = Category.get_active_categories()

        # Sprawdzenie, że zwrócona jest tylko aktywna kategoria
        self.assertEqual(len(active_cats), 1)
        self.assertEqual(active_cats[0].name, "Aktywna")
        self.assertTrue(active_cats[0].is_active)

    # TC5: Dezaktywacja kategorii
    def test_deactivate_category(self):
        name = "X"
        cat = Category.create_category(name, color=None)
        self.assertTrue(cat.is_active)
        Category.deactivate_category(name)
        cat_refreshed = Category.get_all_categories()[0]
        self.assertFalse(cat_refreshed.is_active)

    # TC6: Usuwanie kategorii
    def test_delete_category(self):
        name = "X"
        cat = Category.create_category(name, color=None)
        result = Category.delete_with_expenses(name)
        self.assertTrue(result)
        self.assertEqual(len(Category.get_all_categories()), 0)

    # TC7: Usuwanie nieistniejącej kategorii
    def test_delete_nonexistent_category(self):
        result = Category.delete_with_expenses("Brak")
        self.assertFalse(result)

    # TC8: Unikalność koloru dla nowej kategorii
    def test_unique_color_generation(self):
        # Tworzymy kilka kategorii spoza PASTEL_COLORS
        names = ["X", "Y", "Z"]
        colors = set()
        for n in names:
            c = Category.create_category(n, color=None)
            self.assertNotIn(c.color, colors)
            colors.add(c.color)
        self.assertEqual(len(colors), 3)
