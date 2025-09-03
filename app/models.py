import os
from peewee import *
from datetime import datetime
from database import db
from colors import PASTEL_COLORS


if os.environ.get("TEST_MODE") == "True":
    db = SqliteDatabase(":memory:")
else:
    db = SqliteDatabase("mybudget.db")


class BaseModel(Model):
    class Meta:
        database = db


class Expense(BaseModel):
    amount = FloatField()
    category = CharField()
    date = DateField(default=datetime.now().date)

    @classmethod
    def create_expense(cls, amount, category, date=None):
        if not Category.get_or_none(Category.name == category):
            raise ValueError(f"Kategoria '{category}' nie istnieje lub została usunięta")
        if amount <= 0:
            raise ValueError("Kwota wydatku musi być większa od 0")
        if date is None:
            date = datetime.now().date()
        return cls.create(amount=amount, category=category, date=date)

    @classmethod
    def get_all(cls):
        return list(cls.select().order_by(cls.date.desc()))

    @classmethod
    def get_by_id(cls, id):
        try:
            return cls.get(cls.id == id)
        except DoesNotExist:
            return None

    @classmethod
    def update_expense(cls, id, **kwargs):
        query = cls.update(**kwargs).where(cls.id == id)
        updated = query.execute()
        # UPDATE expense SET amount = 200 WHERE id = 999999999;
        # Jeśli nie ma rekordu o takim id → 0 rows affected
        return cls.get_by_id(id) if updated else None

    @classmethod
    def delete_expense(cls, id):
        query = cls.delete().where(cls.id == id)
        deleted = query.execute()
        return cls.get_by_id(id) if deleted else None


    @classmethod
    def category_summary(cls):
        query = (cls
                 .select(cls.category, fn.SUM(cls.amount).alias('total'))
                 .group_by(cls.category))
        return list(query)

class Category(BaseModel):
    name = CharField(unique=True)
    color = CharField(unique=True)  # Każda kategoria ma swój unikalny kolor
    is_active = BooleanField(default=True)

    @classmethod
    def create_category(cls, name, color=None):
        # Jeśli nazwa jest w PASTEL_COLORS, używamy przypisanego koloru
        if name in PASTEL_COLORS:
            color = PASTEL_COLORS[name]
        else:
            # Generujemy losowy pastelowy kolor, który nie jest jeszcze użyty
            used_colors = [c.color for c in cls.get_all_categories()]
            if color is None:
                color = cls.generate_unique_color(used_colors)
        return cls.create(name=name, color=color, is_active=True)

    @staticmethod
    def generate_unique_color(used_colors):
        import random
        while True:
            r = lambda: random.randint(128, 255)
            color = f'#{r():02X}{r():02X}{r():02X}'
            if color not in used_colors:
                return color

    @classmethod
    def get_all_categories(cls):
        return list(cls.select())

    @classmethod
    def delete_with_expenses(cls, name):
        try:
            cat = cls.select().where(cls.name == name).first()
            if not cat:
                return False  # brak kategorii

            # Usuń wszystkie wydatki w tej kategorii
            Expense.delete().where(Expense.category == name).execute()
            # Usuń kategorię
            cat.delete_instance()
            return True
        except Exception as e:
            print("Błąd usuwania kategorii:", e)
            return False

    @classmethod
    def deactivate_category(cls, name):
        cat = cls.get_or_none(cls.name == name)
        if cat and cat.is_active:
            cat.is_active = False
            cat.save()
            return True
        return False

    @classmethod
    def get_active_categories(cls):
        return cls.select().where(cls.is_active == True)


# # Tworzenie tabel tylko jeśli nie jesteśmy w trybie testowym
# # (w testach tabele będą tworzone przez test setup)
# if not TEST_MODE:
#     db.create_tables([Expense, Category])
db.connect()
db.create_tables([Expense, Category])
