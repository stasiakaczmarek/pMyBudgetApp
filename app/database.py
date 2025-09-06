import os

# Określamy, czy będziemy działać w trybie testowym
# Pobieramy zmienną środowiskową TEST_MODE
# Porównujemy jej wartość (string) do "true"
# Jeśli "true" to uruchamiamy tryb testowy (baza w pamięci, SQLite)
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'

from peewee import PostgresqlDatabase, SqliteDatabase

# Wybieramy bazę danych zależnie od trybu
if TEST_MODE:
    # Tryb testowy: baza w pamięci (SQLite)
    db = SqliteDatabase(':memory:')
else:
    # Tryb produkcyjny: baza PostgreSQL, konfiguracja z zmiennych środowiskowych
    db = PostgresqlDatabase(
        os.getenv('POSTGRES_DB', 'mybudgetdb'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'db'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
    )

def init_db():
    # Inicjalizacja połączenia z bazą
    # Sprawdzamy, czy połączenie jest zamknięte i jeśli tak, otwieramy je
    # Tworzymy tabele na podstawie klas modeli dziedziczących po BaseModel
    try:
        if db.is_closed():
            db.connect()
            print("Połączenie z bazą danych udane!")
        # Tworzymy tabele w bazie na podstawie wszystkich modeli
        from app.models import BaseModel
        db.create_tables(BaseModel.__subclasses__(), safe=True)
    except Exception as e:
        print(f"Błąd połączenia: {e}")

def close_db():
    # Zamykanie połączenia z bazą:
    # Sprawdzamy, czy połączenie jest otwarte, jeśli tak zamykamy
    try:
        if not db.is_closed():
            db.close()
            print("Połączenie z bazą danych zamknięte!")
    except Exception as e:
        print(f"Błąd zamykania połączenia: {e}")
