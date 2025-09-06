# app/tests/tests_MainUnit.py
import unittest
from unittest.mock import patch, MagicMock
import app.main

class TestMain(unittest.TestCase):

    @patch("main.st")
    def test_main_runs(self, mock_st):
        # Mockowanie sidebar i form
        mock_st.sidebar = MagicMock()
        mock_st.sidebar.__enter__ = MagicMock(return_value=mock_st.sidebar)
        mock_st.sidebar.__exit__ = MagicMock(return_value=None)

        mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
        for col in mock_st.columns.return_value:
            col.__enter__ = MagicMock(return_value=col)
            col.__exit__ = MagicMock(return_value=None)

        mock_st.tabs = MagicMock(return_value=[MagicMock()] * 5)
        for tab in mock_st.tabs.return_value:
            tab.__enter__ = MagicMock(return_value=tab)
            tab.__exit__ = MagicMock(return_value=None)

        # Mockowanie metod Streamlit
        methods = ["title", "subheader", "write", "info", "warning", "error",
                   "success", "dataframe", "metric", "number_input", "selectbox",
                   "date_input", "form_submit_button", "plotly_chart", "experimental_rerun", "button", "text_input"]
        for m in methods:
            setattr(mock_st, m, MagicMock())


if __name__ == "__main__":
    unittest.main()
