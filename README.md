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
# Aktywacja środowiska (PowerShell)
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\venv\Scripts\Activate.ps1
```
# Aktywacja środowiska (CMD)
```bash
.\venv\Scripts\activate.bat
```
Po aktywacji powinno być (venv) na początku linii.

### 3. Instalacja zależności

```bash
pip install -r requirements.txt
python -m pip install --upgrade pip setuptools wheel
```

### 4. Inicjalizacja bazy danych (wymagane przy pierwszym uruchomieniu)

```bash
python init_db.py
```
Skrypt utworzy tabele w bazie danych i doda domyślne kategorie.

5. Uruchomienie aplikacji
Dla trybu SQLite (testowego - domyślny):
```bash
$env:TEST_MODE = "true"
streamlit run app/app.py
```
Dla trybu PostgreSQL (opcjonalnie):
Najpierw ustaw zmienne środowiskowe:

```bash
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PASSWORD = "postgres"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_DB = "mybudgetdb"
$env:TEST_MODE = "false"
```
Następnie uruchom aplikację:

```bash
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

