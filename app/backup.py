import pandas as pd
from peewee import fn
from models import Expense, Category
from database import db, TEST_MODE
import os
# from datetime import datetime

ENV_CSV = os.getenv("CSV_FILE")
if ENV_CSV:
    CSV_FILE = ENV_CSV
else:
    # base_dir = katalog nadrzędny względem pliku backup.py (czyli root projektu jeśli backup.py leży w app/)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidates = [
        os.path.join(base_dir, "data", "expenses.csv"),    # ../data/expenses.csv  <- pasuje do Twojego tree
        os.path.join(base_dir, "app", "data", "expenses.csv"),
        os.path.join("/app", "data", "expenses.csv"),      # stary dockerowy path (fallback)
        os.path.join(os.getcwd(), "data", "expenses.csv"),  # ./data/expenses.csv uruchamiając z root
        os.path.join(os.getcwd(), "expenses.csv"),         # ./expenses.csv
    ]
    # wybierz pierwszy istniejący plik; jeśli żaden nie istnieje — użyj pierwszego (pierwszy praktyczny fallback)
    CSV_FILE = next((p for p in candidates if p and os.path.isfile(p)), candidates[0])

def ensure_categories(expenses):
    """
    Sprawdza wszystkie kategorie w Expense i dodaje brakujące do tabeli Category jako aktywne.
    """
    existing_categories = {c.name for c in Category.select()}
    for e in expenses:
        if e.category not in existing_categories:
            Category.create_category(e.category, color=None)  # kolor zostanie przypisany automatycznie
            existing_categories.add(e.category)

def import_from_csv():
    try:
        # Spróbuj różnych kodowań i separatorów
        try:
            df = pd.read_csv(CSV_FILE, sep=',', encoding='utf-8-sig')  # utf-8-sig usuwa BOM
        except:
            try:
                df = pd.read_csv(CSV_FILE, sep=',', encoding='utf-8-sig')
            except:
                df = pd.read_csv(CSV_FILE, sep=',', encoding='latin-1')

        if df.empty:
            print("Plik CSV jest pusty")
            return

        # Normalizuj nazwy kolumn (usuń spacje, zmień na małe litery)
        df.columns = df.columns.str.strip().str.lower()

        expected_cols = {"id", "kwota", "kategoria", "data"}
        if not expected_cols.issubset(set(df.columns)):
            print(f"Niespodziewane kolumny: {df.columns}")

        # Mapowanie nazw kolumn
        column_mapping = {
            'id': 'id',
            'kwota': 'amount',
            'kategoria': 'category',
            'data': 'date'
        }

        # Zmień nazwy kolumn
        df = df.rename(columns=column_mapping)

        print(f"Znalezione kolumny: {list(df.columns)}")
        print(f"Liczba wierszy: {len(df)}")

        with db.atomic():
            for _, row in df.iterrows():
                try:
                    # Konwersja daty z formatu DD.MM.YYYY
                    date_str = str(row["date"])
                    date_obj = pd.to_datetime(date_str).date()

                    # Sprawdź czy rekord już istnieje
                    existing = Expense.get_or_none(Expense.id == int(row["id"]))

                    if existing:
                        # Aktualizuj istniejący rekord
                        existing.amount = float(row["amount"])
                        existing.category = row["category"]
                        existing.date = date_obj
                        existing.save()
                    else:
                        # Dodaj nowy rekord
                        Expense.create(
                            id=int(row["id"]),
                            amount=float(row["amount"]),
                            category=row["category"],
                            date=date_obj
                        )

                except Exception as e:
                    print(f"Błąd przetwarzania wiersza {row}: {e}")
                    print(f"Zawartość wiersza: {row}")
                    continue

        print(f"Import z CSV zakończony. Zaimportowano {len(df)} rekordów.")

        # Pobierz wszystkie wydatki po imporcie
        expenses = list(Expense.select())

        # Upewnij się, że wszystkie kategorie istnieją w tabeli Category
        ensure_categories(expenses)

    except FileNotFoundError:
        print(f"Brak pliku CSV: {CSV_FILE}")
    except Exception as e:
        print(f"Błąd importu CSV: {e}")
        import traceback
        traceback.print_exc()
def export_to_csv():
    try:
        expenses = list(Expense.select().order_by(Expense.date))
        if not expenses:
            pd.DataFrame(columns=["ID", "Kwota", "Kategoria", "Data"]).to_csv(CSV_FILE, index=False)
            return
        df = pd.DataFrame([{
            "ID": e.id,
            "Kwota": e.amount,
            "Kategoria": e.category,
            "Data": e.date
        } for e in expenses])
        df.to_csv(CSV_FILE, index=False)
        print("Eksport do CSV zakończony.")
    except Exception as e:
        print(f"Błąd eksportu CSV: {e}")


print("Aktualna ścieżka CSV:", CSV_FILE)
print("Czy plik istnieje?", os.path.exists(CSV_FILE))


def reset_id_sequence():
    """Resetuje sekwencję ID dla tabeli expense po imporcie CSV"""
    if TEST_MODE:
        print("TEST_MODE: pomijam reset sekwencji ID (SQLite nie wymaga)")
        return

    try:
        with db.atomic():
            max_id = Expense.select(fn.MAX(Expense.id)).scalar() or 0
            db.execute_sql(f"SELECT setval('expense_id_seq', {max_id + 1}, false)")
            print(f"Zresetowano sekwencję ID do: {max_id + 1}")
    except Exception as e:
        print(f"Błąd resetowania sekwencji ID: {e}")