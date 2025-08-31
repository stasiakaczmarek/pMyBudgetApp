# tests_web.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def test_add_expense():
    driver = webdriver.Chrome()
    try:
        driver.get("http://localhost:8501")

        # Poczekaj aż strona się załaduje
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Znajdź input kwoty - Streamlit używa specjalnych atrybutów
        amount_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number']"))
        )
        amount_input.clear()
        amount_input.send_keys("100")

        # Znajdź select kategorii
        category_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select"))
        )
        category_select.send_keys("Zakupy")

        # Znajdź input daty
        date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='date']"))
        )
        date_input.send_keys("2024-05-01")

        # Znajdź przycisk submit - Streamlit może używać różnych selektorów
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Dodaj wydatek')]"))
        )
        submit_button.click()

        time.sleep(2)  # Poczekaj na reakcję

        # Sprawdź czy pojawił się komunikat sukcesu
        success_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stToast']")
        assert len(success_elements) > 0, "Brak komunikatu sukcesu"

    finally:
        driver.quit()


def test_navigation_tabs():
    driver = webdriver.Chrome()
    try:
        driver.get("http://localhost:8501")

        # Poczekaj aż strona się załaduje
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Znajdź zakładki - Streamlit używa specjalnych klas
        tabs = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='stTab']"))
        )

        assert len(tabs) >= 5, f"Znaleziono tylko {len(tabs)} zakładek zamiast 5"

        # Kliknij każdą zakładkę
        for i, tab in enumerate(tabs):
            try:
                tab.click()
                time.sleep(1)  # Poczekaj na zmianę zawartości
                print(f"Kliknięto zakładkę {i + 1}")
            except Exception as e:
                print(f"Błąd przy klikaniu zakładki {i + 1}: {e}")

    finally:
        driver.quit()

