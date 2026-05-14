import pickle
import pandas as pd

def predict_sales(data):

    with open("models/model.pkl", "rb") as f:
        model = pickle.load(f)

    with open("models/columns.pkl", "rb") as f:
        cols = pickle.load(f)

    data = pd.get_dummies(data)

    data = data.reindex(
        columns=cols,
        fill_value=0
    )

    pred = model.predict(data)

    return pred