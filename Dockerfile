# Użyta wersja Pythona
FROM python:3.9-slim


# Ustaw katalog roboczy wewnątrz kontenera na /app
WORKDIR /app

# Konkretne wersje numpy i pandas
RUN pip install numpy==1.24.3 pandas==1.5.3

# Reszta wymagań
COPY requirements.txt .
# Zapobiega zapisywaniu paczek w pamięci podręcznej, co zmniejsza rozmiar obrazu
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy całą zawartość folderu app/ do katalogu roboczego w kontenerze
COPY . /app

# Domyślne polecenie uruchamiające aplikację Streamlit
# CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]