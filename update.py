import os
import requests
import pandas as pd
from datetime import datetime, timedelta

API_KEY = os.environ["EOD_API_KEY"]

BASE_URL = "https://eodhd.com/api"

os.makedirs("data", exist_ok=True)

etfs = pd.read_csv("etfs.csv")


def download_history(code):

    url = f"{BASE_URL}/eod/{code}"

    params = {
        "api_token": API_KEY,
        "fmt": "json",
        "period": "d",
        "from": "2010-01-01"
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    data = r.json()

    df = pd.DataFrame(data)

    df = df.rename(columns={
        "date": "Date",
        "adjusted_close": "Close"
    })

    df = df[["Date", "Close"]]

    df["Date"] = pd.to_datetime(df["Date"])

    return df


def update_history(isin):

    filename = f"data/{isin}.csv"

    new = download_history(isin)

    if os.path.exists(filename):

        old = pd.read_csv(filename)
        old["Date"] = pd.to_datetime(old["Date"])

        df = pd.concat([old, new])

        df = (
            df
            .drop_duplicates("Date")
            .sort_values("Date")
        )

    else:
        df = new

    df.to_csv(filename, index=False)

    return df


results = []

for _, row in etfs.iterrows():

    isin = row["ISIN"]

    df = update_history(isin)

    close = df["Close"]

    price = close.iloc[-1]

    result = {
        "Date": datetime.today().strftime("%Y-%m-%d"),
        "ISIN": isin,
        "Name": row["Name"],
        "Price": round(price, 2),
    }

    for days in [200, 250, 300]:

        sma = close.rolling(days).mean().iloc[-1]

        result[f"SMA{days}"] = round(sma, 2)
        result[f"Above{days}"] = (
            "YES" if price > sma else "NO"
        )

    results.append(result)


pd.DataFrame(results).to_csv(
    "results.csv",
    index=False
)
