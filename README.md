# Aplikacja do śledzenia wydatków

Aplikacja webowa napisana w **Streamlit** z wykorzystaniem **Peewee ORM** i bazy danych **PostgreSQL** (w produkcji) lub **SQLite** (w trybie testowym). Umożliwia:

* dodawanie wydatków,
* zarządzanie kategoriami,
* analizę trendów,
* eksport/import danych z pliku CSV,
* interaktywne wykresy (Plotly).

---

## 🔧 Uruchomienie lokalne

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/stasiakaczmarek/pMyBudgetApp.git
cd pMyBudgetApp
```

### 2. Utworzenie i aktywacja środowiska wirtualnego

```bash
python -m venv venv
source venv/bin/activate   # Linux/MacOS
venv\Scripts\activate      # Windows
```

### 3. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 4. Zmienna środowiskowa (opcjonalna)

Jeżeli chcesz korzystać z PostgreSQL, ustaw dane dostępowe:

```bash
export POSTGRES_DB=mybudgetdb
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
```

W przeciwnym wypadku, aplikacja uruchomi się w trybie **SQLite** (TEST\_MODE).

### 5. Uruchomienie aplikacji

```bash
streamlit run app/main.py
```

Aplikacja będzie dostępna pod adresem: [http://localhost:8501](http://localhost:8501)

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

### 3. (Opcjonalnie) Uruchomienie z docker-compose

Jeśli posiadasz plik `docker-compose.yml`, uruchom cały zestaw (aplikacja + PostgreSQL):

```bash
docker-compose up --build
```

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

