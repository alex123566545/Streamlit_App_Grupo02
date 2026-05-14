import streamlit as st
import pandas as pd
from utils.database import get_connection

st.title("📊 Dashboard")

conn = get_connection()

query = """
SELECT *
FROM gold_ml.ventas_predicha
LIMIT 100
"""

df = pd.read_sql(query, conn)

st.dataframe(df)

st.metric(
    label="Total Predicciones",
    value=len(df)
)

st.metric(
    label="Promedio Predicción",
    value=round(df["cantidad_predicha"].mean(), 2)
)