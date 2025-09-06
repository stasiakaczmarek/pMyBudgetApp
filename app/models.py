import os
from peewee import *
from datetime import datetime
from database import db
from colors import PASTEL_COLORS

# Wybieramy bazę danych w zależności od trybu
if os.environ.get("TEST_MODE") == "True":
    # Baza w pamięci dla testów (ulotna, szybka)
    db = SqliteDatabase(":memory:")
else:
    # db = SqliteDatabase("mybudget.db")
    # Lokalna baza Postgres do normalnego działania
    db = PostgresqlDatabase(
        os.getenv('POSTGRES_DB', 'mybudgetdb'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'db'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
    )

# Klasa bazowa dla wszystkich modeli (Expense, Category)
class BaseModel(Model):
    class Meta:
        # Każdy model używa tej samej bazy danych
        database = db

# Model reprezentujący pojedynczy wydatek
class Expense(BaseModel):
    # Kwota wydatku
    amount = FloatField()
    # Nazwa kategorii (string)
    category = CharField()
    # Data wydatku (domyślnie dzisiejsza)
    date = DateField(default=datetime.now().date)

    @classmethod
    def create_expense(cls, amount, category, date=None):
        # Walidacja: czy kategoria istnieje i jest aktywna
        if not Category.get_or_none(Category.name == category):
            raise ValueError(f"Kategoria '{category}' nie istnieje lub została usunięta")
        # Walidacja: kwota musi być dodatnia
        if amount <= 0:
            raise ValueError("Kwota wydatku musi być większa od 0")
        # Jeśli data nie jest podana ustaw dzisiejszą
        if date is None:
            date = datetime.now().date()
        # Tworzymy wpis w bazie
        return cls.create(amount=amount, category=category, date=date)

    @classmethod
    def get_all(cls):
        # Pobieramy wszystkie wydatki posortowane malejąco po dacie
        return list(cls.select().order_by(cls.date.desc()))

    @classmethod
    def get_by_id(cls, id):
        # Pobieramy wydatek po ID lub None jeśli nie istnieje
        try:
            return cls.get(cls.id == id)
        except DoesNotExist:
            return None

    @classmethod
    def update_expense(cls, id, **kwargs):
        # Aktualizacja wydatku po ID
        query = cls.update(**kwargs).where(cls.id == id)
        updated = query.execute()
        # UPDATE expense SET amount = 200 WHERE id = 999999999;
        # Jeśli nie ma rekordu o takim id to zwraca 0 rows affected
        # Zwracamy nową wersję wpisu jeśli coś się zmieniło, w przeciwnym razie None
        return cls.get_by_id(id) if updated else None

    @classmethod
    def delete_expense(cls, id):
        # Usunięcie wydatku po ID
        query = cls.delete().where(cls.id == id)
        deleted = query.execute()
        # Zwracamy nową wersję wpisu jeśli coś się zmieniło, w przeciwnym razie None
        return cls.get_by_id(id) if deleted else None

    @classmethod
    def category_summary(cls):
        # Sumowanie wydatków według kategorii
        query = (cls
                 .select(cls.category, fn.SUM(cls.amount).alias('total'))
                 .group_by(cls.category))
        return list(query)

# Model reprezentujący kategorię wydatków
class Category(BaseModel):
    # Unikalna nazwa kategorii
    name = CharField(unique=True)
    # Kolor przypisany kategorii
    # Każda kategoria ma swój unikalny kolor
    color = CharField(unique=True)
    # Flaga aktywności (można dezaktywować kategorię)
    is_active = BooleanField(default=True)

    @classmethod
    def create_category(cls, name, color=None):
        # Jeśli kategoria istnieje w PASTEL_COLORS, użyj przypisanego koloru
        if name in PASTEL_COLORS:
            color = PASTEL_COLORS[name]
        else:
            # W przeciwnym razie losujemy unikalny pastelowy kolor
            used_colors = [c.color for c in cls.get_all_categories()]
            if color is None:
                color = cls.generate_unique_color(used_colors)
        return cls.create(name=name, color=color, is_active=True)

    # Generator losowych pastelowych kolorów
    @staticmethod
    def generate_unique_color(used_colors):
        import random
        while True:
            r = lambda: random.randint(128, 255)
            color = f'#{r():02X}{r():02X}{r():02X}'
            # Sprawdzamy czy kolor już nie istnieje
            if color not in used_colors:
                return color

    # Pobramy wszystkie kategorie
    @classmethod
    def get_all_categories(cls):
        return list(cls.select())

    # Usunięcie kategorii wraz ze wszystkimi powiązanymi wydatkami
    @classmethod
    def delete_with_expenses(cls, name):
        try:
            cat = cls.select().where(cls.name == name).first()
            if not cat:
                return False

            # Najpierw usuwamy wszystkie wydatki w tej kategorii
            Expense.delete().where(Expense.category == name).execute()
            # Potem usuwamy kategorie
            cat.delete_instance()
            return True
        except Exception as e:
            print("Błąd usuwania kategorii:", e)
            return False

    @classmethod
    def deactivate_category(cls, name):
        # Dezaktywacja kategorii (ustawienie is_active=False)
        cat = cls.get_or_none(cls.name == name)
        if cat and cat.is_active:
            cat.is_active = False
            cat.save()
            return True
        return False

    @classmethod
    def get_active_categories(cls):
        # Pobieramy wszystkie aktywne kategorie
        return cls.select().where(cls.is_active == True)


# Inicjalizacja połączenia z bazą
db.connect()
db.create_tables([Expense, Category])
