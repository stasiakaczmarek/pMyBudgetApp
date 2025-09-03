# Import biblioteki Streamlit do tworzenia aplikacji webowych
import streamlit as st
# Import biblioteki pandas do pracy z danymi tabelarycznymi
import pandas as pd
# Import biblioteki plotly.express do tworzenia interaktywnych wykresów
import plotly.express as px
# Import klasy Expense z pliku models.py – reprezentuje pojedynczy wydatek
from models import Expense, Category
# Import funkcji inicjalizującej bazę danych
from database import init_db
from backup import import_from_csv, export_to_csv, CSV_FILE
from colors import PASTEL_COLORS
from categories import DEFAULT_CATEGORIES
from polish_months import POLISH_MONTHS

def main():

    import os

    with st.sidebar:
        st.write("CSV_FILE:", CSV_FILE)
        st.write("CSV istnieje?", os.path.isfile(CSV_FILE))

    # Inicjalizacja połączenia z bazą danych
    init_db()

    with st.sidebar:
        st.subheader("Diagnostyka")
        try:
            # import loguje do konsoli; poniżej dorzucamy licznik z bazy
            import_from_csv()
            from backup import reset_id_sequence
            reset_id_sequence()
            try:
                total = Expense.select().count()
            except Exception as e:
                total = 0
                st.error(f"Błąd zapytania do bazy po imporcie: {e}")
            st.info(f"Liczba rekordów w bazie po imporcie: {total}")
            if total == 0:
                st.warning("Brak danych w bazie. Sprawdź, czy CSV jest pod /app/data/expenses.csv (lub zmień ścieżkę w backup.py).")
        except Exception as e:
            st.error(f"Błąd importu CSV: {e}")

    # Funkcja zwracająca listę dostępnych kategorii
    def get_categories():
        cats = [c.name for c in Category.get_all_categories()]
        return [c for c in cats if Category.get_or_none(Category.name == c)]

    def monthly_expenses_by_category():
        try:
            # Pobierz wszystkie wydatki
            expenses = Expense.select()
            if not expenses:
                st.info("Brak danych do wyświetlenia")
                return

            # Konwertuj do DataFrame
            expense_df = pd.DataFrame([e.__data__ for e in expenses])
            expense_df['date'] = pd.to_datetime(expense_df['date'])

            # Dodaj kolumnę z polską nazwą miesiąca (ZMIANA: użyj string zamiast Period)
            expense_df['month_period'] = expense_df['date'].dt.to_period('M')
            expense_df['month_str'] = expense_df['month_period'].astype(str)
            expense_df['month_polish'] = expense_df['date'].dt.month.map(POLISH_MONTHS) + ' ' + expense_df[
                'date'].dt.year.astype(str)

            # Wybór miesiąca (ZMIANA: użyj month_str zamiast month_period)
            available_months = sorted(expense_df['month_str'].unique(), reverse=True)
            selected_month_str = st.selectbox(
                "Wybierz miesiąc",
                options=available_months,
                format_func=lambda x: f"{POLISH_MONTHS[int(x.split('-')[1])]} {x.split('-')[0]}"
            )

            # Filtruj dane dla wybranego miesiąca
            filtered_df = expense_df[expense_df['month_str'] == selected_month_str]

            if filtered_df.empty:
                year, month = selected_month_str.split('-')
                polish_month_name = f"{POLISH_MONTHS[int(month)]} {year}"
                st.info(f"Brak wydatków dla {polish_month_name}")
                return

            # Grupuj po kategorii i sumuj kwoty
            category_summary = filtered_df.groupby('category')['amount'].sum().reset_index()
            category_summary = category_summary.sort_values('amount', ascending=False)

            # Wyświetl podsumowanie
            year, month = selected_month_str.split('-')
            polish_month_name = f"{POLISH_MONTHS[int(month)]} {year}"
            st.subheader(f"Suma wszystkich wydatków w {polish_month_name}")

            # Tabela z wydatkami
            st.dataframe(
                category_summary.rename(columns={
                    'category': 'Kategoria',
                    'amount': 'Kwota'
                }).set_index('Kategoria')
            )

            categories_in_data = filtered_df['category'].unique()
            color_map = {}
            for cat in categories_in_data:
                c = Category.get_or_none(Category.name == cat)
                if c:
                    color_map[cat] = c.color
                else:
                    c = Category.create_category(cat, color=None)
                    color_map[cat] = c.color

            # Wykres słupkowy
            fig = px.bar(
                category_summary,
                x='category',
                y='amount',
                title=f"Podział wydatków według kategorii – {polish_month_name}",
                labels={'category': 'Kategoria', 'amount': 'Kwota (zł)'},
                color='category',
                color_discrete_map=color_map
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Podsumowanie ogólne
            total = category_summary['amount'].sum()
            st.metric("Łączna kwota", f"{total:.2f} zł")

        except Exception as e:
            st.error(f"Błąd podczas przetwarzania danych: {str(e)}")

    def manage_expenses():
        try:
            expenses = list(Expense.select().order_by(Expense.date.desc()))
            if not expenses:
                st.warning("Brak wydatków. Dodaj pierwszy wydatek w formularzu powyżej.")
                return

            # Tabela
            expense_df = pd.DataFrame([{
                'ID': e.id,
                'Kwota': e.amount,
                'Kategoria': e.category,
                'Data': e.date,
            } for e in expenses])
            st.dataframe(expense_df.set_index('ID'))

            # Wpisanie ID wydatku ręcznie
            first_id = expenses[0].id if expenses else 1
            selected_id = st.number_input(
                "Wpisz ID wydatku do edycji/usunięcia",
                min_value=1,
                step=1,
                value=first_id
            )

            # Sprawdzenie czy wydatek istnieje
            expense_to_edit = Expense.get_or_none(Expense.id == selected_id)
            if not expense_to_edit:
                st.info("Nie znaleziono wydatku o takim ID.")
                return

            col1, col2 = st.columns(2)

            with col1:
                # Formularz edycji
                with st.form("edit_expense"):
                    old_amount = expense_to_edit.amount
                    old_category = expense_to_edit.category

                    new_amount = st.number_input("Kwota", value=expense_to_edit.amount, min_value=0.01, step=0.01)
                    new_category = st.selectbox("Kategoria", get_categories(), index=get_categories().index(expense_to_edit.category))
                    new_date = st.date_input("Data", value=expense_to_edit.date)

                    if st.form_submit_button("Zapisz zmiany"):
                        old_amount = expense_to_edit.amount
                        old_category = expense_to_edit.category
                        old_date = expense_to_edit.date

                        expense_to_edit.amount = new_amount
                        expense_to_edit.category = new_category
                        expense_to_edit.date = new_date
                        expense_to_edit.save()
                        export_to_csv()

                        # Tworzymy komunikat tylko z faktycznych zmian
                        msg_lines = [f"Wydatek ID {selected_id} zaktualizowany:"]
                        if old_amount != new_amount:
                            msg_lines.append(f"- Kwota: {old_amount:.2f} → {new_amount:.2f}")
                        if old_category != new_category:
                            msg_lines.append(f"- Kategoria: '{old_category}' → '{new_category}'")
                        if old_date != new_date:
                            msg_lines.append(f"- Data: {old_date} → {new_date}")

                        # Jeśli nic się nie zmieniło, pokaż informację
                        if len(msg_lines) == 1:
                            msg_lines.append("Brak zmian.")

                        st.success("\n".join(msg_lines))

            with col2:
                col2a, col2b = st.columns(2)  # Dwie kolumny w kolumnie col2: jedna na Usuń, druga na Odśwież

                with col2a:
                    if st.button("Usuń wydatek", key="delete_button"):
                        category = expense_to_edit.category
                        amount = expense_to_edit.amount
                        Expense.delete_expense(selected_id)
                        export_to_csv()
                        st.success(
                            f"Usunięto wydatek ID {selected_id} w kategorii '{category}' "
                            f"o kwocie {amount:.2f} zł"
                        )
                        st.session_state["selected_expense"] = None
                        st.experimental_rerun()

                with col2b:
                    if st.button("Odśwież listę wydatków", key="refresh_button"):
                        st.experimental_rerun()

        except Exception as e:
            st.error(f"Błąd ładowania danych: {str(e)}")


    def manage_categories():
        # Pobierz wszystkie kategorie z bazy
        all_categories = [c.name for c in Category.get_all_categories()]
        active_categories = [c.name for c in Category.get_active_categories()]

        # --- Dodawanie nowej kategorii ---
        with st.form("add_category_form"):
            new_category = st.text_input("Nowa kategoria")
            if st.form_submit_button("Dodaj kategorię"):
                if not new_category:
                    st.warning("Podaj nazwę kategorii!")
                elif new_category in all_categories:
                    st.warning("Ta kategoria już istnieje!")
                else:
                    try:
                        Category.create_category(new_category)
                        st.success(f"Dodano kategorię: {new_category}")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Błąd dodawania kategorii: {e}")

        # --- Usuwanie kategorii wraz z wydatkami ---
        with st.form("remove_category_form"):
            category_to_remove = st.selectbox(
                "Wybierz kategorię do usunięcia",
                all_categories,
                key="remove_category_select"
            )
            if st.form_submit_button("Usuń kategorię"):
                try:
                    deleted = Category.delete_with_expenses(category_to_remove)
                    if deleted:
                        export_to_csv()  # Zaktualizuj CSV
                        st.success(
                            f"Usunięto kategorię i wszystkie wydatki w niej zawarte: {category_to_remove}"
                        )
                    else:
                        st.warning("Nie znaleziono kategorii")
                except Exception as e:
                    st.error(f"Błąd usuwania kategorii: {e}")
                st.experimental_rerun()

        # --- Dezaktywacja kategorii ---
        if active_categories:
            with st.form("deactivate_category_form"):
                category_to_deactivate = st.selectbox(
                    "Wybierz kategorię do dezaktywacji",
                    active_categories,
                    key="deactivate_category_select"
                )
                if st.form_submit_button("Dezaktywuj kategorię"):
                    try:
                        if Category.deactivate_category(category_to_deactivate):
                            st.success(f"Kategoria '{category_to_deactivate}' została dezaktywowana")
                            st.experimental_rerun()
                        else:
                            st.warning(f"Kategoria '{category_to_deactivate}' nie mogła zostać dezaktywowana")
                    except Exception as e:
                        st.error(f"Błąd dezaktywacji kategorii: {e}")
        else:
            st.info("Brak aktywnych kategorii do dezaktywacji")

        # --- Aktywacja kategorii ---
        inactive_categories = [c.name for c in Category.get_all_categories() if not c.is_active]
        if inactive_categories:
            with st.form("activate_category_form"):
                category_to_activate = st.selectbox(
                    "Wybierz kategorię do aktywacji",
                    inactive_categories,
                    key="activate_category_select"
                )
                if st.form_submit_button("Aktywuj kategorię"):
                    try:
                        cat = Category.get_or_none(Category.name == category_to_activate)
                        if cat:
                            cat.is_active = True
                            cat.save()
                            st.success(f"Kategoria '{category_to_activate}' została aktywowana")
                        else:
                            st.warning("Nie znaleziono kategorii")
                    except Exception as e:
                        st.error(f"Błąd aktywacji kategorii: {e}")
                    st.experimental_rerun()
        else:
            st.info("Brak nieaktywnych kategorii do aktywacji")


    def average_monthly_expense_by_category():
        expenses = Expense.select()
        if not expenses:
            st.info("Brak danych do wyświetlenia")
            return

        df = pd.DataFrame([e.__data__ for e in expenses])
        df['date'] = pd.to_datetime(df['date'])

        # Wyodrębnij rok i miesiąc
        df['year_month'] = df['date'].dt.to_period('M')

        # Suma wydatków miesięcznie po kategorii
        monthly_sum = df.groupby(['year_month', 'category'])['amount'].sum().reset_index()

        # Średnia miesięczna po kategorii
        avg_df = monthly_sum.groupby('category')['amount'].mean().reset_index()
        avg_df = avg_df.rename(columns={'amount': 'Średni wydatek (zł)', 'category': 'Kategoria'})
        avg_df = avg_df.sort_values('Średni wydatek (zł)', ascending=False)

        st.subheader("Średni miesięczny wydatek według kategorii")
        st.dataframe(avg_df.set_index('Kategoria'))
        return avg_df

    # Tytuł aplikacji
    st.title("Śledź swoje wydatki")

    # Formularz do dodawania nowego wydatku

    with st.form("new_expense"):
        amount = st.number_input("Kwota", min_value=0.01, step=0.01)

        # Pobieramy tylko aktywne kategorie
        active_categories = [c.name for c in Category.get_active_categories()]
        if not active_categories:
            st.warning("Brak aktywnych kategorii. Dodaj lub aktywuj kategorię przed dodaniem wydatku.")
        else:
            category = st.selectbox("Kategoria", options=active_categories)
            date = st.date_input("Data")

            if st.form_submit_button("Dodaj wydatek"):
                try:
                    Expense.create_expense(amount=amount, category=category, date=date)
                    export_to_csv()
                    st.success("Wydatek dodany!")
                    st.experimental_rerun()
                except ValueError as e:
                    st.error(f"Niepoprawny wydatek: {e}")


    # Zmień linię tworzącą zakładki na:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Podsumowanie", "Analiza trendów", "Miesięczne wydatki", "Zarządzanie wydatkami", "Zarządzanie kategoriami"])

    # Zawartość pierwszej zakładki - Podsumowanie
    with tab1:
        # Pobieramy wszystkie wydatki i dokonujemy konwersji do DataFrame
        expenses = Expense.select()
        expense_df = pd.DataFrame([e.__data__ for e in expenses])
        categories_in_data = expense_df['category'].unique()
        color_map = {}
        for cat in categories_in_data:
            # Pobierz obiekt kategorii z bazy
            c = Category.get_or_none(Category.name == cat)
            if c:
                color_map[cat] = c.color
            else:
                # Jeśli kategorii nie ma w bazie, stwórz ją z unikalnym kolorem
                c = Category.create_category(cat, color=None)
                color_map[cat] = c.color

        if not expense_df.empty:
            # Konwersja daty do formatu datetime i wyodrębnienie miesiąca
            expense_df['date'] = pd.to_datetime(expense_df['date'])
            # expense_df['month'] = expense_df['date'].dt.to_period('M')

            # Dodaj polskie nazwy miesięcy (używaj tylko stringów)
            expense_df['month_str'] = expense_df['date'].dt.to_period('M').astype(str)
            expense_df['month_polish'] = expense_df['date'].dt.month.map(POLISH_MONTHS) + ' ' + expense_df[
                'date'].dt.year.astype(str)

            # Grupowanie danych po stringach zamiast Period
            monthly_df = expense_df.groupby(['month_str', 'month_polish', 'category'])['amount'].sum().reset_index()
            monthly_df = monthly_df.sort_values('month_str')

            # PRZED tworzeniem fig (bar) i fig_pie:
            category_df = expense_df.groupby('category')['amount'].sum().reset_index()

            # Kolejność: od największej do najmniejszej
            category_order = (category_df.sort_values('amount', ascending=False)['category'].tolist()
            )

            # Dodajemy kolumnę datetime dla pierwszego dnia miesiąca
            monthly_df['month_date'] = pd.to_datetime(monthly_df['month_str'] + '-01')

            # Sortowanie po dacie
            monthly_df = monthly_df.sort_values('month_date')

            # Wykres
            fig = px.bar(
                monthly_df,
                x='month_polish',  # dalej pokazujemy polskie nazwy
                y='amount',
                color='category',
                barmode='stack',
                title="Struktura wydatków według kategorii (miesięcznie)",
                labels={'month_polish': 'Miesiąc', 'amount': 'Kwota (zł)', 'category': 'Kategoria'},
                color_discrete_map=color_map,
                category_orders={'category': category_order}
            )

            # Ustawienie osi x w kolejności daty
            fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': monthly_df['month_polish'].tolist()})
            fig.update_xaxes(tickangle=-45)
            fig.update_layout(
                legend=dict(
                    # Pionowa orientacja
                    orientation="v",
                    yanchor="top",
                    # Górna krawędź
                    y=1,
                    xanchor="left",
                    # Po prawej stronie wykresu
                    x=1.02,
                    # Szerokość elementów
                    itemwidth=30,
                    # Rozmiar czcionki
                    font=dict(size=9)
                ),
                # Mrgines prawy
                margin=dict(r=180),
                # Wysokość wykresu
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
            category_df = expense_df.groupby('category')['amount'].sum().reset_index()

            # Wykres kołowy
            fig_pie = px.pie(
                category_df,
                values='amount',
                names='category',
                title="Udział procentowy kategorii w całkowitych wydatkach",
                # Używamt kategorii jako kolorów
                color='category',
                color_discrete_map=color_map,
                # Dodajemy dziurę w środku dla lepszej czytelności
                hole=0.3,
                category_orders = {'category': category_order}
            )

            # TE SAME USTAWIENIA CO DLA WYKRESU SŁUPKOWEGO:
            fig_pie.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    itemwidth=30,
                    font=dict(size=9)
                ),
                margin=dict(r=180, t=250),
                height=720)
            st.plotly_chart(fig_pie, use_container_width=True)

        else:
            st.info("Brak danych do wyświetlenia")

    # Zawartość drugiej zakładki - Trendy
    with tab2:
        expenses = Expense.select().order_by(Expense.date)
        if expenses:
            trend_df = pd.DataFrame([e.__data__ for e in expenses])

            # Konwersja daty do formatu datetime
            trend_df['date'] = pd.to_datetime(trend_df['date'])

            # Dodaj polskie nazwy miesięcy
            trend_df['month_str'] = trend_df['date'].dt.to_period('M').astype(str)
            trend_df['month_polish'] = trend_df['date'].dt.month.map(POLISH_MONTHS) + ' ' + trend_df['date'].dt.year.astype(
                str)

            # Suma skumulowana
            trend_df['cumulative'] = trend_df['amount'].cumsum()

            # Wykres trendu skumulowanego
            fig_trend = px.line(trend_df,
                                x='date',
                                y='cumulative',
                                title='Narastająca suma wydatków w czasie',
                                labels={'date': 'Miesiąc', 'cumulative': 'Suma skumulowana (zł)'})

            # Pobierz unikalne daty z danych
            unique_dates = trend_df['date'].dt.to_period('M').unique().astype('datetime64[M]')

            # Utwórz polskie etykiety
            polish_labels = [f"{POLISH_MONTHS[date.month]} {date.year}" for date in unique_dates]

            # Zastosuj niestandardowe etykiety
            fig_trend.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=unique_dates,
                    ticktext=polish_labels,
                    tickangle=-45
                )
            )

            st.plotly_chart(fig_trend)

            # Wydatki miesięczne
            monthly_trend = trend_df.copy()
            monthly_summary = monthly_trend.groupby(['month_str', 'month_polish'])['amount'].sum().reset_index()
            monthly_summary = monthly_summary.sort_values('month_str')

            fig_monthly = px.line(monthly_summary,
                                  x='month_polish',
                                  y='amount',
                                  title='Łączne wydatki w poszczególnych miesiącach',
                                  labels={'month_polish': 'Miesiąc', 'amount': 'Suma wydatków (zł)'},
                                  markers=True)
            fig_monthly.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_monthly)
        else:
            st.info("Brak danych do analizy trendów")

    # Zawartość trzeciej zakładki - Wydatki miesięczne
    with tab3:
        monthly_expenses_by_category()

        # Wywołanie funkcji i tworzenie wykresu
        avg_df = average_monthly_expense_by_category()
        if avg_df is not None and not avg_df.empty:
            fig_avg = px.bar(
                avg_df,
                x='Kategoria',
                y='Średni wydatek (zł)',
                title="Średni miesięczny wydatek po kategorii",
                labels={'category': 'Kategoria', 'Średni wydatek (zł)': 'Średni wydatek (zł)'},
                color='Średni wydatek (zł)',  # Kolorowanie słupków według wartości
                color_continuous_scale='Viridis'  # Ładna skala kolorów
            )

            # Poprawa układu wykresu
            fig_avg.update_layout(
                xaxis_tickangle=-45,
                height=500,  # Wysokość wykresu
                showlegend=False
            )

            # Formatowanie osi Y (waluta)
            fig_avg.update_yaxes(tickprefix="zł ", tickformat=",.0f")

            st.plotly_chart(fig_avg, use_container_width=True)

    # Zawartość czwartej zakładki - Zarządzanie wydatkami
    with tab4:
        manage_expenses()

    # Zawartość piątej zakładki - Zarządzanie kategoriami
    with tab5:
        manage_categories()

if __name__ == "__main__":
    main()

