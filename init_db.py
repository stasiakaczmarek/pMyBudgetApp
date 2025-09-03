import os

# Włącz tryb testowy (SQLite)New-Item -Path . -Name "init_db.py" -ItemType "file"
os.environ['TEST_MODE'] = 'true'

from app.database import db
from app.main import Expense, Category


# Utwórz tabele
db.create_tables([Expense, Category])
print('Tabele utworzone pomyślnie!')

# Dodaj domyślne kategorie
default_categories = [
    'Jedzenie', 'Transport', 'Rozrywka', 'Mieszkanie', 'Zdrowie',
    'Zakupy spożywcze', 'Wakacje', 'Ubrania', 'Trening', 'Torebki',
    'Taksówki', 'Słodycze', 'Samochód', 'Rzęsy', 'Restauracje',
    'Prezenty', 'Pielęgnacja', 'Paznokcie', 'Odpoczynek', 'Nauka',
    'Makijaż', 'Komunikacja miejska', 'Inwestycje', 'Inne', 'Fastfoody',
    'Elektronika', 'Czystość', 'Buty', 'Biżuteria'
]

for cat_name in default_categories:
    Category.get_or_create(name=cat_name, defaults={'is_active': True})

print('Domyślne kategorie dodane!')
