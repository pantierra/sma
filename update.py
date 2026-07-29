import os
import requests
import pandas as pd
from datetime import datetime

API_KEY = os.environ["EOD_API_KEY"]

BASE_URL = "https://eodhd.com/api"

os.makedirs("data", exist_ok=True)

etfs = pd.read_csv("etfs.csv")


def download_history(code):
    """
    Download EODHD price history using EODHD symbol.
    Example:
    XZW0.XETRA
    """

    url = f"{BASE_URL}/eod/{code}"

    params = {
        "api_token": API_KEY,
        "fmt": "json",
        "period": "d",
        "from": "2010-01-01",
    }

    r = requests.get(url, params=params)

    if r.status_code != 200:
        raise RuntimeError(
            f"EODHD request failed for {code}\n"
            f"URL: {r.url}\n"
            f"Status: {r.status_code}\n"
            f"Response: {r.text}"
        )

    data = r.json()

    if not data:
        raise RuntimeError(f"No price data returned for {code}")

    df = pd.DataFrame(data)

    df = df.rename(
        columns={
            "date": "Date",
            "adjusted_close": "Close",
        }
    )

    if "Date" not in df.columns or "Close" not in df.columns:
        raise RuntimeError(
            f"Unexpected EODHD response for {code}: {df.columns.tolist()}"
        )

    df = df[["Date", "Close"]]

    df["Date"] = pd.to_datetime(df["Date"])
    df["Close"] = pd.to_numeric(df["Close"])

    return df


def update_history(isin, eod_code):
    """
    Update local history CSV.
    """

    filename = f"data/{isin}.csv"

    new = download_history(eod_code)

    if os.path.exists(filename):

        old = pd.read_csv(filename)
        old["Date"] = pd.to_datetime(old["Date"])

        df = pd.concat(
            [old, new],
            ignore_index=True
        )

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
    eod_code = row["EOD_Code"]

    print(f"Updating {row['Name']} ({eod_code})")

    df = update_history(isin, eod_code)

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

        result[f"SMA{days}"] = (
            round(sma, 2)
            if pd.notna(sma)
            else None
        )

        result[f"Above{days}"] = (
            "YES"
            if pd.notna(sma) and price > sma
            else "NO"
        )

    results.append(result)


pd.DataFrame(results).to_csv(
    "results.csv",
    index=False
)

print("Update completed successfully.")
