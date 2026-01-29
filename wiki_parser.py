import requests
import re
from bs4 import BeautifulSoup

WIKI_URL = "https://pl.wikipedia.org/wiki/ISO_4217"

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'application/json',
    }

def clean_currency_name(name: str) -> str:
    return re.sub(r"\[\d+\]", "", name).strip()


def fetch_wiki_soup() -> BeautifulSoup:
    r = requests.get(WIKI_URL, headers=headers, timeout=10)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def parse_currencies(soup: BeautifulSoup) -> list[dict]:
    table = soup.select_one("table.wikitable")
    if not table:
        raise RuntimeError("Currency table not found")

    currencies = []

    for row in table.select("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        code = cols[0].text.strip()[:3]
        name = clean_currency_name(cols[3].text)

        if code in {"XXX", "XTS"}:
            continue

        currencies.append(
            {
                "code": code,
                "name": name,
            }
        )

    return currencies
