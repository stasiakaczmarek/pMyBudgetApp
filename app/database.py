import os
from peewee import PostgresqlDatabase, SqliteDatabase

# Określ, czy jesteśmy w trybie testowym
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'

if TEST_MODE:
    # Użyj SQLite dla testów
    db = SqliteDatabase(':memory:')  # Baza w pamięci
else:
    # Użyj PostgreSQL dla normalnego działania
    db = PostgresqlDatabase(
        os.getenv('POSTGRES_DB', 'mybudgetdb'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'db'),
        port=5432
    )

def init_db():
    try:
        db.connect()
        print("Połączenie z bazą danych udane!")
    except Exception as e:
        print(f"Błąd połączenia: {e}")