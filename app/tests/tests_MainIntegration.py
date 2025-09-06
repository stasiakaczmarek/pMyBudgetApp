import pytest
from datetime import date
from models import Expense, Category
from database import init_db
from backup import export_to_csv, import_from_csv, reset_id_sequence
import os
import pandas as pd


@pytest.fixture(scope="function")
def setup_db():
    init_db(':memory:')
    yield


def test_full_flow(tmp_path, setup_db):
    # 1️⃣ Dodaj kategorię i wydatki
    cat1 = Category.create_category("Jedzenie")
    cat2 = Category.create_category("Transport")
    e1 = Expense.create_expense(100, cat1.name, date(2025, 1, 1))
    e2 = Expense.create_expense(50, cat2.name, date(2025, 1, 2))

    # 2️⃣ Eksport do CSV
    csv_file = tmp_path / "expenses.csv"
    from backup import CSV_FILE as backup_csv_file
    import backup
    backup.CSV_FILE = str(csv_file)
    export_to_csv()
    assert os.path.isfile(csv_file)

    # 3️⃣ Usuń wszystkie wydatki i zresetuj sekwencję
    Expense.delete_expense(e1.id)
    Expense.delete_expense(e2.id)
    reset_id_sequence()
    assert Expense.select().count() == 0

    # 4️⃣ Import z CSV
    import_from_csv()
    assert Expense.select().count() == 2

    # 5️⃣ Obliczenia miesięczne
    expenses = Expense.select()
    df = pd.DataFrame([e.__data__ for e in expenses])
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_sum = df.groupby(['year_month', 'category'])['amount'].sum().reset_index()

    assert monthly_sum.shape[0] == 2  # dwie kategorie
    assert monthly_sum[monthly_sum['category'] == "Jedzenie"]['amount'].values[0] == 100
    assert monthly_sum[monthly_sum['category'] == "Transport"]['amount'].values[0] == 50

    # Przywracamy oryginalną ścieżkę
    backup.CSV_FILE = backup_csv_file
