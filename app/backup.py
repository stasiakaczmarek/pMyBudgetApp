from datetime import datetime
import pandas as pd
from peewee import fn
from models import Expense, Category
from database import db, TEST_MODE
import os
import logging

# Dodajemy logger
logger = logging.getLogger(__name__)

# Dlaczego w backup.py potrzebujemy loggera?
# 1. Inny rodzaj operacji
# models.py - operacje na bazie danych - błędy są rzucane jako wyjątki
# backup.py - operacje na plikach i transformacje danych - potrzebujemy logować błędy, a nie tylko je rzucać
# 2. Inna filozofia obsługi błędów
# W models.py
# def create_expense(amount, category, date):
   # if amount <= 0:
# Rzuca wyjątek
       # raise ValueError("Kwota musi być większa od 0")

# W backup.py
# def import_from_csv():
   # try:
    # Może failować na wiele sposobów
       # df = pd.read_csv(CSV_FILE)
   # except Exception as e:
       # Loguje błą
       # logger.error(f"Błąd importu CSV: {e}")
       # Ale nie przerywa działania aplikacji


# Ustalamy ścieżkę pliku csv
# najpierw sprawdzana jest zmienna środowiskowa CSV_FILE
# jeśli brak, wybierane są różne możliwe lokalizacje pliku
ENV_CSV = os.getenv("CSV_FILE")
if ENV_CSV:
    CSV_FILE = ENV_CSV
else:
    # base_dir = katalog nadrzędny względem pliku backup.py (czyli root projektu jeśli backup.py leży w app/)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ""))
    candidates = [
        os.path.join(base_dir, "../data", "expenses.csv"),    # ../data/expenses.csv  <- pasuje do Twojego tree
        os.path.join(base_dir, "", "data", "expenses.csv"),
        os.path.join("", "data", "expenses.csv"),      # stary dockerowy path (fallback)
        os.path.join(os.getcwd(), "../data", "expenses.csv"),  # ./data/expenses.csv uruchamiając z root
        os.path.join(os.getcwd(), "expenses.csv"),         # ./expenses.csv
    ]
    # Wybieramy pierwszy istniejący plik
    # Jeśli żaden nie istnieje — użyj pierwszego
    CSV_FILE = next((p for p in candidates if p and os.path.isfile(p)), candidates[0])

def ensure_categories(expenses):
    # Sprawdzamy, czy wszystkie kategorie z Expenses istnieją w tabeli Category
    # Jeśli brakuje jakiejś kategorii, zostaje ona dodana z domyślnym kolorem
    existing_categories = {c.name for c in Category.select()}

    for e in expenses:
        if e.category not in existing_categories:
            # Kolor zostanie przypisany automatycznie
            Category.create_category(e.category, color=None)
            existing_categories.add(e.category)

def import_from_csv(csv_file=None):
# Importujemy dane z pliku CSV do bazy
# Próbujemy odczytać plik na wszelki wypadek w kilku kodowaniach
# Normalizujemy nazwy kolumn (PL i EN)
# Tworzymy/aktualizujemy rekordy w bazie
# Pomijamy błędne lub niekompletne wiersze

    try:
        path_to_use = csv_file or CSV_FILE
        logger.info(f"Importuję CSV z: {path_to_use}")

        # Próba odczytu w różnych kodowaniach
        try:
            df = pd.read_csv(path_to_use, sep=',', encoding='utf-8')
        except Exception:
            try:
                df = pd.read_csv(path_to_use, sep=',', encoding='utf-8-sig')
            except Exception:
                df = pd.read_csv(path_to_use, sep=',', encoding='latin-1')

        # Dodajemy obsługę pustego pliku
        if df.empty:
            logger.info("Plik CSV jest pusty")
            return 0

        # Czyścimy nagłówki kolumn
        df.columns = df.columns.str.strip().str.replace('\ufeff', '').str.lower()

        # Dodajemy obsługę różnych wariantów nagłówków
        possible_mappings = [
            {"id": "id", "kwota": "amount", "kategoria": "category", "data": "date"},  # polskie
            {"id": "id", "amount": "amount", "category": "category", "date": "date"}  # angielskie
        ]

        for mapping in possible_mappings:
            if set(mapping.keys()).issubset(set(df.columns)):
                df = df.rename(columns=mapping)
                break
        else:
            logger.error(f"Niespodziewane kolumny: {df.columns}")
            return 0

        logger.info(f"Znalezione kolumny: {list(df.columns)}")
        logger.info(f"Liczba wierszy w CSV: {len(df)}")

        imported_count = 0

        with db.atomic():
            for _, row in df.iterrows():
                try:
                    # Dodajemy pomijanie niekompletnych danych
                    if pd.isna(row["amount"]) or pd.isna(row["date"]) or pd.isna(row["category"]):
                        logger.warning(f"Pomijam wiersz z brakującymi danymi: {row}")
                        continue

                    # Dodajemy parsowanie daty
                    try:
                        date_obj = pd.to_datetime(str(row["date"]), errors='raise').date()
                    except Exception:
                        logger.warning(f"Niepoprawna data, pomijam wiersz: {row}")
                        continue

                    # Aktualizujemy istniejące wydatki lub tworzymy nowe
                    existing = Expense.get_or_none(Expense.id == int(row["id"]))
                    if existing:
                        existing.amount = float(row["amount"])
                        existing.category = row["category"]
                        existing.date = date_obj
                        existing.save()
                    else:
                        Expense.create(
                            id=int(row["id"]),
                            amount=float(row["amount"]),
                            category=row["category"],
                            date=date_obj
                        )
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Błąd przetwarzania wiersza {row}: {e}")
                    continue

        logger.info(f"Import z CSV zakończony. Zaimportowano {imported_count} rekordów.")

        # Uzupełnienie kategorii w tabeli Category
        expenses = list(Expense.select())
        ensure_categories(expenses)

        return imported_count

    except FileNotFoundError:
        logger.error(f"Brak pliku CSV: {path_to_use}")
        return 0
    except Exception as e:
        logger.error(f"Błąd importu CSV: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def export_to_csv():
    # Eksportujemy wszystkie wydatki z bazy do pliku CSV
    # Sortujemy po dacie
    # Zapisujemy z nagłówkami w języku polskim
    try:
        expenses_query = list(Expense.select().order_by(Expense.date))
        # Dopiero teraz konwertujemy do listy
        expense_list = list(expenses_query)
        if not expense_list:
            pd.DataFrame(columns=["ID", "Kwota", "Kategoria", "Data"]).to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
            logger.info("Eksport pustej bazy do CSV zakończony.")
            return

        # Budumey dataframe na podstawie obiektów Expense
        df = pd.DataFrame([{
            "ID": e.id,
            "Kwota": e.amount,
            "Kategoria": e.category,
            "Data": e.date
        } for e in expense_list])

        # Zapisujemy do csvki
        df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
        logger.info(f"Eksport do CSV zakończony. Wyeksportowano {len(expense_list)} rekordów.")
    except Exception as e:
        logger.error(f"Błąd eksportu CSV: {e}")
        import traceback
        logger.error(traceback.format_exc())

print("Aktualna ścieżka CSV:", CSV_FILE)
print("Czy plik istnieje?", os.path.exists(CSV_FILE))


def reset_id_sequence():
    # Resetujemy sekwencję ID w Postgresie na podstawie największego id w tabeli Expense
    # Dla SQLite w trybie TEST_MODE nie jest to wymamgane
    if TEST_MODE:
        logger.info("TEST_MODE: pomijam reset sekwencji ID (SQLite nie wymaga)")
        return

    try:
        with db.atomic():
            max_id = Expense.select(fn.MAX(Expense.id)).scalar() or 0
            seq_name = Expense._meta.table_name + "_id_seq"

            # Reset sekwencji tylko jeśli istnieje w Postgresie
            db.execute_sql(f"""
                        DO $$
                        BEGIN
                            IF EXISTS (SELECT 1 FROM pg_class WHERE relname = '{seq_name}') THEN
                                PERFORM setval('{seq_name}', {max_id + 1}, false);
                            END IF;
                        END $$;
                        """)

            logger.info(f"Zresetowano sekwencję ID ({seq_name}) do: {max_id + 1}")
    except Exception as e:
        logger.error(f"Błąd resetowania sekwencji ID: {e}")
