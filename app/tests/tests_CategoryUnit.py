import os
import unittest
from unittest.mock import patch, MagicMock

# Ustawienie trybu testowego
os.environ['TEST_MODE'] = 'True'

from models import Category

class TestCategoryWithMock(unittest.TestCase):

    def setUp(self):
        # Patchowanie metod Category używających bazy danych
        self.get_all_patch = patch('models.Category.get_all_categories')
        self.get_active_patch = patch('models.Category.get_active_categories')
        self.create_patch = patch('models.Category.create_category')
        self.delete_with_expenses_patch = patch('models.Category.delete_with_expenses')
        self.deactivate_patch = patch('models.Category.deactivate_category')

        # Start patchy
        self.mock_get_all = self.get_all_patch.start()
        self.mock_get_active = self.get_active_patch.start()
        self.mock_create = self.create_patch.start()
        self.mock_delete_with_expenses = self.delete_with_expenses_patch.start()
        self.mock_deactivate = self.deactivate_patch.start()

        # TC1: Tworzenie przykładowego obiekti Category z kolorem zdefiniowanym w PASTEL_COLORS
        self.sample_category = MagicMock()
        self.sample_category.name = "Zakupy"
        self.sample_category.color = "#FFD700"
        self.sample_category.is_active = True

    def tearDown(self):
        patch.stopall()

    # TC2: Tworzenie kategorii z losowym kolorem (nie w PASTEL_COLORS)
    def test_create_category_with_random_color_logic(self):
        from models import Category

        new_category = MagicMock()
        new_category.name = "X"

        # Zakładamy, że pewne kolory już istnieją
        used_colors = ["#FFFFFF", "#000000", "#FF0000"]

        # Wywołanie metody generate_unique_color
        new_color = Category.generate_unique_color(used_colors)

        # Sprawdzenie, że zwrócony kolor jest unikalny
        self.assertNotIn(new_color, used_colors)

        new_category.color = new_color
        new_category.is_active = True
        self.mock_create.return_value = new_category
        cat = Category.create_category("X")
        self.assertEqual(cat.name, "X")
        self.assertTrue(cat.is_active)

    # TC3: Pobranie wszystkich kategorii (mock)
    def test_get_all_categories(self):
        self.mock_get_all.return_value = [self.sample_category]
        categories = Category.get_all_categories()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].name, "Zakupy")
        self.assertTrue(categories[0].is_active)

    # TC4: Pobranie tylko aktywnych kategorii (mock)
    def test_get_active_categories(self):
        self.mock_get_active.return_value = [self.sample_category]
        active = Category.get_active_categories()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].name, "Zakupy")
        self.assertTrue(active[0].is_active)

    # TC5: Dezaktywacja kategorii (mock)
    def test_deactivate_category(self):
        self.mock_deactivate.return_value = True
        result = Category.deactivate_category("Zakupy")
        self.assertTrue(result)

        self.mock_deactivate.return_value = False
        result = Category.deactivate_category("Nieaktywowalna")
        self.assertFalse(result)

    # TC6: Usuwanie kategorii wraz z wydatkami (mock)
    def test_delete_with_expenses(self):
        self.mock_delete_with_expenses.return_value = True
        result = Category.delete_with_expenses("Zakupy")
        self.assertTrue(result)

        self.mock_delete_with_expenses.return_value = False
        result = Category.delete_with_expenses("Nieistniejąca")
        self.assertFalse(result)

    # TC7: Usuwanie nieistniejącej kategorii (mock)
    def test_delete_nonexistent_category(self):
        self.mock_delete_with_expenses.return_value = False
        result = Category.delete_with_expenses("Brak")
        self.assertFalse(result)

    # TC8: Generowanie unikalnego koloru (bez bazy danych)
    def test_generate_unique_color(self):
        from models import Category
        used_colors = ["#FFFFFF", "#000000"]
        color = Category.generate_unique_color(used_colors)
        self.assertNotIn(color, used_colors)
        self.assertTrue(color.startswith("#"))
        self.assertEqual(len(color), 7)