import streamlit as st
import pandas as pd

from utils.database import get_connection

st.title("📜 Historial")

conn = get_connection()

query = """
SELECT *
FROM gold_ml.ventas_predicha
ORDER BY fecha DESC
LIMIT 50
"""

df = pd.read_sql(query, conn)

st.dataframe(df)