import os
os.environ['TEST_MODE'] = 'True'

import unittest
from models import Category, Expense
from database import db
from colors import PASTEL_COLORS


class TestCategory(unittest.TestCase):
    # Każdy test startuje na świeżej, in-memory bazie SQLite.

    def setUp(self):
        # Przygotowujemy bazę przed każdym testem, czyli
        # Tworzymy połączenie z bazą w pamięci
        db.connect()
        # Tworzymy tabele Expense i Category
        db.create_tables([Expense, Category])

    def tearDown(self):
        # Czyszczenie bazy po każdym teście, aby każdy test zaczynał z pustą bazą
        if not db.is_closed():
            db.drop_tables([Expense, Category])
            db.close()

    # TC1: Tworzenie kategorii z kolorem zdefiniowanym w PASTEL_COLORS
    def test_create_category_with_preset_color(self):
        # Test sprawdza, że:
        # metoda create_category przypisuje kolor z PASTEL_COLORS, jeśli nazwa jest w słowniku
        # -nowa kategoria ma is_active=True
        name = "Biżuteria"
        cat = Category.create_category(name, color=None)
        self.assertEqual(cat.name, name)
        self.assertEqual(cat.color, PASTEL_COLORS[name])
        self.assertTrue(cat.is_active)
        # MA SENS, prawdza faktyczne przypisanie koloru i status aktywności w bazie

    # TC2: Tworzenie kategorii z losowym kolorem (nie w PASTEL_COLORS)
    def test_create_category_with_random_color(self):
        # Test sprawdza:
        # generowanie koloru, który nie powtarza się w PASTEL_COLORS,
        # unikalność w bazie,
        # poprawny format koloru,
        #aktywność kategorii.

        from colors import PASTEL_COLORS

        name = "X"

        # Zbieramy wszystkie istniejące kolory w bazie i PASTEL_COLORS
        existing_colors = set(c.color for c in Category.get_all_categories())
        existing_colors.update(PASTEL_COLORS.values())

        # Tworzymy nową kategorię bez podanego koloru
        cat = Category.create_category(name, color=None)

        # Sprawdzenie, że kolor nie powtarza się z istniejącymi
        self.assertNotIn(cat.color, existing_colors)

        # Sprawdzenie formatu koloru '#RRGGBB'
        self.assertTrue(cat.color.startswith("#"))
        # Sprawdzamy długość stringa reprezentującego kolor
        self.assertEqual(len(cat.color), 7)

        # Sprawdzenie nazwy i aktywności
        self.assertEqual(cat.name, name)
        self.assertTrue(cat.is_active)
        # MA SENS, faktycznie testuje logikę generowania koloru i zapis w bazie

    # TC3: Pobieranie wszystkich kategorii
    def test_get_all_categories(self):
        # Testuje, czy get_all_categories zwraca wszystkie kategorie z bazy
        Category.create_category("X", color=None)
        Category.create_category("Y", color=None)
        cats = Category.get_all_categories()
        self.assertEqual(len(cats), 2)
        self.assertListEqual(sorted([c.name for c in cats]), ["X", "Y"])
        # MA SENS, srawdza integrację z bazą

    # TC4: Pobieranie tylko aktywnych kategorii
    def test_get_active_categories(self):
        # Testuje logikę filtrowania aktywnych kategorii
        cat1 = Category.create_category("Aktywna", color=None)
        cat2 = Category.create_category("Nieaktywna", color=None)
        Category.deactivate_category("Nieaktywna")

        active_cats = Category.get_active_categories()
        self.assertEqual(len(active_cats), 1)
        self.assertEqual(active_cats[0].name, "Aktywna")
        self.assertTrue(active_cats[0].is_active)
        # TROCHĘ NACIĄGANY ale niby testuje specyficzną funkcję get_active_categories

    # TC5: Dezaktywacja kategorii
    def test_deactivate_category(self):
        # Testuje, czy deactivate_category faktycznie ustawia is_active=False
        name = "X"
        cat = Category.create_category(name, color=None)
        self.assertTrue(cat.is_active)
        Category.deactivate_category(name)
        cat_refreshed = Category.get_all_categories()[0]
        self.assertFalse(cat_refreshed.is_active)
        # MA SENS, weryfikuje zmianę statusu w bazie

    # TC6: Usuwanie kategorii wraz z wydatkami
    def test_delete_category(self):
        # Testuje czy delete_with_expenses:
        # usuwa kategorię
        # weryfikuje, że nie ma jej w bazie
        name = "X"
        cat = Category.create_category(name, color=None)
        result = Category.delete_with_expenses(name)
        self.assertTrue(result)
        self.assertEqual(len(Category.get_all_categories()), 0)
        # MA SENS, sprawdza usuwanie i integralność danych

    # TC7: Usuwanie nieistniejącej kategorii
    def test_delete_nonexistent_category(self):
        result = Category.delete_with_expenses("Brak")
        self.assertFalse(result)
        # SZTUCZNY w integracyjnych testach, kontroluje tylko zwracanie False, jeśli brak rekordu

    # TC8: Unikalność koloru dla nowej kategorii
    def test_unique_color_generation(self):
        # Sprawdza, czy każda nowa kategoria dostaje unikalny kolor:
        # względem istniejących już kategorii w bazie,
        # względem kolorów zdefiniowanych w PASTEL_COLORS.

        from colors import PASTEL_COLORS

        # Zbieramy wszystkie istniejące kolory w bazie i PASTEL_COLORS
        existing_colors = set(c.color for c in Category.get_all_categories())
        existing_colors.update(PASTEL_COLORS.values())

        # Tworzymy nowe kategorie z losowym kolorem
        names = ["X", "Y", "Z"]
        for n in names:
            c = Category.create_category(n, color=None)
            # Sprawdzamy, że kolor nowej kategorii nie powtarza się z istniejącymi
            self.assertNotIn(c.color, existing_colors)
            # Dodajemy nowy kolor do zbioru istniejących
            existing_colors.add(c.color)
            # Sprawdzamy, że kolor wygląda jak '#RRGGBB'
            # Sprawdzamy długość stringa reprezentującego kolor
            self.assertTrue(c.color.startswith("#"))
            self.assertEqual(len(c.color), 7)
            # Kategoria powinna być aktywna
            self.assertTrue(c.is_active)
            # MA SENS, sprawdza generowanie koloru, zapis w bazie, sprawdzenie unikalności względem wszystkich kategorii i PASTEL_COLORS

