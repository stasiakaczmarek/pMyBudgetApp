# Aplikacja do śledzenia wydatków

Aplikacja webowa napisana w **Streamlit** z wykorzystaniem **Peewee ORM** i bazy danych **PostgreSQL** (w produkcji) lub **SQLite** (w trybie testowym). Umożliwia:

* dodawanie wydatków,
* zarządzanie kategoriami,
* analizę trendów,
* eksport/import danych z pliku CSV,
* interaktywne wykresy.

---

## Uruchomienie lokalne

### 1. Klonowanie repozytorium
Jeżeli folder pMyBudgetApp już istnieje, pomiń git clone i przejdź do folderu projektu.

```bash
# 1. Bądź w folderze nadrzędnym (pMyBudgetApp)
cd C:\Users\Anastasia\PycharmProjects\pMyBudgetApp
```
```bash
# 2. Sklonuj repozytorium (jeżeli jeszcze nie sklonowane)
git clone https://github.com/stasiakaczmarek/pMyBudgetApp.git
```
```bash
# 3. Przejdź do folderu z projektem
cd pMyBudgetApp
```

### 2. Utworzenie i aktywacja środowiska wirtualnego
Jeżeli już masz venv, pomiń tworzenie.

```bash
# Utworzenie środowiska (tylko za pierwszym razem)
python -m venv venv
```
```bash
# Aktywacja środowiska
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1
```
Po aktywacji powinno być (venv) na początku linii.

### 3. Instalacja zależności

```bash
pip install -r requirements.txt
python -m pip install --upgrade pip setuptools wheel
```

### 4. Inicjalizacja bazy danych (wymagane przy pierwszym uruchomieniu)
Jeżeli nie istnieje:
```bash
New-Item -Path . -Name "init_db.py" -ItemType "file"
```
Otwórz plik init_db.py w edytorze (np. PyCharm) i wklej:

"import os
from app.database import db
from app.models import Expense, Category
os.environ['TEST_MODE'] = 'true'
db.create_tables([Expense, Category])
print('Tabele utworzone pomyślnie!')
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
print('Domyślne kategorie dodane!')"

```bash
python init_db.py
```
Po wykonaniu można opcjonalnie usunąć plik:
```bash
Remove-Item init_db.py
```

5. Zmienna środowiskowa (opcjonalna)
Jeżeli chcesz korzystać z PostgreSQL, ustaw dane dostępowe:

```bash
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PASSWORD = "postgres"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_DB = "mybudgetdb"
```
W przeciwnym wypadku, aplikacja uruchomi się w trybie SQLite (TEST_MODE).

6. Uruchomienie aplikacji

```bash
# Dla trybu SQLite (testowego)
$env:TEST_MODE = "true"
streamlit run app/app.py
```

```bash
# Dla trybu PostgreSQL
streamlit run app/app.py
```

Aplikacja będzie dostępna pod adresem: http://localhost:8501



## Uruchomienie w Dockerze

### 1. Budowa obrazu

```bash
docker build -t wydatki-app .
```

### 2. Uruchomienie kontenera

```bash
docker run -d \
  -p 8501:8501 \
  -e POSTGRES_DB=mybudgetdb \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_HOST=db \
  -v $(pwd)/data:/app/data \
  --name wydatki-app \
  wydatki-app
```

### 3. (Opcjonalnie) Uruchomienie z docker-compose

Jeśli posiadasz plik `docker-compose.yml`, uruchom cały zestaw (aplikacja + PostgreSQL):

```bash
docker-compose up --build
```

Aplikacja będzie dostępna pod adresem: [http://localhost:8501](http://localhost:8501)
---

## Struktura projektu

```
.
├── app/
│   ├── main.py          # Główna aplikacja Streamlit
│   ├── models.py        # Modele Peewee (Expense, Category)
│   ├── database.py      # Konfiguracja bazy (Postgres/SQLite)
│   ├── backup.py        # Import/eksport CSV
│   ├── colors.py        # Paleta kolorów dla kategorii
│   └── data/expenses.csv # Domyślny plik CSV z wydatkami
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Funkcjonalności

* Podsumowania wydatków miesięcznych,
* Średnie wydatki wg kategorii,
* Trendy wydatków w czasie,
* Zarządzanie kategoriami (dodawanie, usuwanie, blokowanie),
* Eksport/Import do pliku CSV.

