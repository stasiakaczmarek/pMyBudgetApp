import os

# Określ, czy jesteśmy w trybie testowym
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'

from peewee import PostgresqlDatabase, SqliteDatabase

if TEST_MODE:
    db = SqliteDatabase(':memory:')  # Baza w pamięci dla testów
else:
    db = PostgresqlDatabase(
        os.getenv('POSTGRES_DB', 'mybudgetdb'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'db'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
    )

def init_db():
    """Funkcja do inicjalizacji połączenia z bazą danych"""
    try:
        if db.is_closed():
            db.connect()
            print("Połączenie z bazą danych udane!")
        # Tworzenie tabel (tylko dla Peewee)
        from app.models import BaseModel  # zakładam, że wszystkie modele dziedziczą po BaseModel
        db.create_tables(BaseModel.__subclasses__(), safe=True)
    except Exception as e:
        print(f"Błąd połączenia: {e}")

def close_db():
    """Funkcja do zamykania połączenia z bazą danych"""
    try:
        if not db.is_closed():  # <- poprawione
            db.close()
            print("Połączenie z bazą danych zamknięte!")
    except Exception as e:
        print(f"Błąd zamykania połączenia: {e}")
