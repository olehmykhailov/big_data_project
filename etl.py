from datetime import date, timedelta
import requests
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from database.db import SessionLocal
from database.models import CurrencyRate, GoldPrice, Currency
from nbp_client import (
    fetch_currency_rate_latest,
    fetch_currency_rates_history,
    fetch_gold_price_latest,
    fetch_gold_prices_history,
)

START_DATE = date(2020, 1, 1)
END_DATE = date.today()
CHUNK_DAYS = 365


# ----------------------------
# Helpers
# ----------------------------
def split_date_range(start: date, end: date, days: int = CHUNK_DAYS):
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=days - 1), end)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)

def save_currencies(session, csv_path: str = "currencies.csv"):
    currencies = pd.read_csv(csv_path).to_dict(orient="records")

    currency_rows = [
        {
            "code": c["code"].strip().upper(),
            "name": c["name"].strip(),
            "table_type": c["table"].strip().upper()
        }
        for c in currencies
    ]

    stmt = insert(Currency).values(currency_rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["code"])
    session.execute(stmt)
    session.commit()

    
# ============================
# DAILY ETL (latest only)
# ============================
def run_daily_etl(session, load_currencies: bool, load_gold: bool, csv_path: str = "currencies.csv"):

    try:
        if load_currencies:
            currencies = pd.read_csv(csv_path).to_dict(orient="records")

            # -------- currencies --------
            rate_rows = []

            for c in currencies:
                code = c["code"].strip().upper()
                table = c["table"].strip().upper()

                latest = fetch_currency_rate_latest(code, table)
                if latest:
                    rate_rows.append(latest)

            if rate_rows:
                stmt = insert(CurrencyRate).values(rate_rows)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["currency_code", "rate_date"]
                )
                session.execute(stmt)
        if load_gold:
        # -------- gold --------
            gold = fetch_gold_price_latest()
            if gold:
                stmt = insert(GoldPrice).values(gold)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["price_date"]
                )
                session.execute(stmt)

            session.commit()
            print("✅ Daily ETL finished")

    except SQLAlchemyError as e:
        session.rollback()
        print("❌ Daily ETL failed:", e)
        raise


# ============================
# HISTORICAL ETL
# ============================
def run_historical_currency_etl(
    session,
    csv_path: str,
    start_date: date,
    end_date: date,
    batch_size: int = 1000,
):
    currencies = pd.read_csv(csv_path).to_dict(orient="records")
    rate_rows = []

    for c in currencies:
        code = c["code"].strip().upper()
        table = c["table"].strip().upper()

        print(f"[CURRENCY] Fetching history for {code}")

        for start, end in split_date_range(start_date, end_date):
            try:
                rates = fetch_currency_rates_history(code, table, start, end)
            except requests.exceptions.HTTPError as e:
                print(e)
                continue
            rate_rows.extend(rates)

            if len(rate_rows) >= batch_size:
                stmt = insert(CurrencyRate).values(rate_rows)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["currency_code", "rate_date"]
                )
                session.execute(stmt)
                session.commit()
                rate_rows.clear()

    if rate_rows:
        stmt = insert(CurrencyRate).values(rate_rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["currency_code", "rate_date"]
        )
        session.execute(stmt)
        session.commit()


# ============================
# HISTORICAL GOLD
# ============================
def run_historical_gold_etl(
    session,
    start_date: date,
    end_date: date,
):
    gold_rows = []

    print("[GOLD] Fetching historical prices")

    for start, end in split_date_range(start_date, end_date):
        gold_rows.extend(fetch_gold_prices_history(start, end))

    if gold_rows:
        stmt = insert(GoldPrice).values(gold_rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["price_date"]
        )
        session.execute(stmt)
        session.commit()


# ============================
# HISTORICAL ORCHESTRATOR
# ============================
def run_historical_etl(
    session,
    csv_path: str,
    start_date: date,
    end_date: date,
    load_currencies: bool,
    load_gold: bool
):
    

    try:
        if load_currencies:
            run_historical_currency_etl(
                session=session,
                csv_path=csv_path,
                start_date=start_date,
                end_date=end_date,
            )
        if load_gold:
            run_historical_gold_etl(
                session=session,
                start_date=start_date,
                end_date=end_date,
            )

        print("✅ Historical ETL finished successfully")

    except SQLAlchemyError as e:
        session.rollback()
        print("❌ Historical ETL failed:", e)
        raise


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="NBP ETL Process")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize static data (currencies)")
    init_parser.add_argument("--csv-path", default="currencies.csv", help="Path to currencies CSV")

    # Command: daily
    daily_parser = subparsers.add_parser("daily", help="Run daily ETL for latest data")
    daily_parser.add_argument("--csv-path", default="currencies.csv", help="Path to currencies CSV")
    daily_parser.add_argument("--skip-currencies", action="store_true", help="Skip downloading currency rates")
    daily_parser.add_argument("--skip-gold", action="store_true", help="Skip downloading gold prices")

    # Command: history
    history_parser = subparsers.add_parser("history", help="Run historical ETL")
    history_parser.add_argument("--start", type=date.fromisoformat, help="Start date (YYYY-MM-DD), default: 2020-01-01")
    history_parser.add_argument("--end", type=date.fromisoformat, help="End date (YYYY-MM-DD), default: today")
    history_parser.add_argument("--csv-path", default="currencies.csv", help="Path to currencies CSV")
    history_parser.add_argument("--skip-currencies", action="store_true", help="Skip downloading currency rates")
    history_parser.add_argument("--skip-gold", action="store_true", help="Skip downloading gold prices")

    args = parser.parse_args()

    session = SessionLocal()
    try:
        if args.command == "init":
            save_currencies(session, args.csv_path)
            print("Database initialized with currencies.")

        elif args.command == "daily":
            run_daily_etl(
                session,
                load_currencies=not args.skip_currencies,
                load_gold=not args.skip_gold,
                csv_path=args.csv_path
            )

        elif args.command == "history":
            start_date = args.start or START_DATE
            end_date = args.end or END_DATE
            run_historical_etl(
                session,
                csv_path=args.csv_path,
                start_date=start_date,
                end_date=end_date,
                load_currencies=not args.skip_currencies,
                load_gold=not args.skip_gold
            )

    except Exception as e:
        print(f"Error details: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()
