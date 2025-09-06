# Aplikacja do śledzenia wydatków

Aplikacja webowa napisana w **Streamlit** z wykorzystaniem **Peewee ORM** i bazy danych **PostgreSQL** (w produkcji) lub **SQLite** (w trybie testowym).

---

## Funkcjonalności

* Struktura wydatków według kategorii (miesięcznie),
* Udział procentowy kategorii w całkowitych wydatkach,
* Narastająca suma wydatków w czasie,
* Łączne wydatki w poszczególnych miesiącach,
* Suma wszystkich wydatków z wyszczególnieniem kategorii,
* Średnie miesięczne wydatki według kategorii,
* Zarządzanie kategoriami (dodawanie, usuwanie, aktywacja, dezaktywacja),
* Zarządzanie wydatkami (dodawanie, usuwanie, edycja),
* Eksport/Import do pliku CSV.

---

## Struktura projektu

```
├── app/
│   ├── tests/ 
│   ├── __init__.py
│   ├── backup.py   
│   ├── categories.py        
│   ├── colors.py      
│   ├── database.py        
│   ├── main.py  
│   ├── models.py  
│   ├── polish_months.py          
│   └── 
├── data/
├── init_db.py.txt
├── docker-compose.yml.txt
├── Dockerfile
└── README.md
```

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
Aktywacja środowiska (PowerShell)

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\venv\Scripts\Activate.ps1
```
Aktywacja środowiska (CMD)

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

### 5. Uruchomienie aplikacji
Dla trybu SQLite (testowego - domyślny):
```bash
$env:TEST_MODE = "true"
streamlit run app/main.py
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
streamlit run app/main.py
```

Aplikacja będzie dostępna pod adresem: http://localhost:8501

---

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

### 3. Uruchomienie z docker-compose

Jeśli posiadasz plik `docker-compose.yml`, uruchom cały zestaw (aplikacja + PostgreSQL):

```bash
docker-compose up --build
```
Aplikacja będzie dostępna pod adresem: http://localhost:8501

