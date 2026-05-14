import pandas as pd

def preprocess_input(df):

    df["fecha"] = pd.to_datetime(df["fecha"])

    df["mes"] = df["fecha"].dt.month

    df["dia_semana"] = df["fecha"].dt.dayofweek

    return df