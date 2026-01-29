import requests
from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional

BASE_URL = "https://api.nbp.pl/api"
NBP_GOLD_URL = f"{BASE_URL}/cenyzlota"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "nbp-etl/1.0",
}


# =========================
# Валюты
# =========================
def fetch_table_codes(table: str, timeout: int = 10) -> set[str]:
    r = requests.get(
        f"{BASE_URL}/exchangerates/tables/{table}/",
        headers=HEADERS,
        timeout=timeout,
    )
    r.raise_for_status()
    return {rate["code"] for rate in r.json()[0]["rates"]}


def fetch_currency_rates_history(
    code: str,
    table: str,
    start: date,
    end: date,
    timeout: int = 10,
) -> List[Dict]:
    url = f"{BASE_URL}/exchangerates/rates/{table}/{code}/{start}/{end}/"
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    result = []

    for item in data["rates"]:
        value = item.get("mid") or item.get("bid") or item.get("ask")
        result.append(
            {
                "currency_code": code,
                "rate_date": date.fromisoformat(item["effectiveDate"]),
                "rate": Decimal(str(value)),
            }
        )

    return result


def fetch_currency_rate_latest(
    code: str,
    table: str,
    timeout: int = 10,
) -> Optional[Dict]:
    url = f"{BASE_URL}/exchangerates/rates/{table}/{code}/"
    r = requests.get(url, headers=HEADERS, timeout=timeout)

    if r.status_code == 404:
        return None

    r.raise_for_status()
    data = r.json()
    item = data["rates"][0]

    value = item.get("mid") or item.get("bid") or item.get("ask")

    return {
        "currency_code": code,
        "rate_date": date.fromisoformat(item["effectiveDate"]),
        "rate": Decimal(str(value)),
    }


# =========================
# Золото
# =========================
def fetch_gold_prices_history(
    start_date: date,
    end_date: date,
    timeout: int = 10,
) -> List[Dict]:
    url = f"{NBP_GOLD_URL}/{start_date}/{end_date}/"
    r = requests.get(url, headers=HEADERS, timeout=timeout)

    if r.status_code == 404:
        return []

    r.raise_for_status()
    data = r.json()

    return [
        {
            "price_date": date.fromisoformat(item["data"]),
            "price_pln": Decimal(str(item["cena"])),
        }
        for item in data
    ]


def fetch_gold_price_latest(timeout: int = 10) -> Optional[Dict]:
    r = requests.get(NBP_GOLD_URL, headers=HEADERS, timeout=timeout)

    if r.status_code == 404:
        return None

    r.raise_for_status()
    item = r.json()[0]

    return {
        "price_date": date.fromisoformat(item["data"]),
        "price_pln": Decimal(str(item["cena"])),
    }
