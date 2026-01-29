from db import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import select
import argparse
import pandas as pd
import pathlib
import os
from models import CurrencyRate

QUERIED_DATA_PATH = pathlib.Path(__file__).parent.parent / "queried_data"
os.makedirs(QUERIED_DATA_PATH, exist_ok=True)

def get_all_currency_data(session: Session, currency_code) -> list[CurrencyRate]:
    with SessionLocal as session:
        stmt = select(CurrencyRate).where(CurrencyRate.currency_code == currency_code)
        results = session.execute(stmt).scalars().all()
        return results

def get_historical_currency_data(session: Session, currency_code, start_date, end_date) -> list[CurrencyRate]:
    with SessionLocal as session:
        stmt = select(CurrencyRate).where(
            CurrencyRate.currency_code == currency_code,
            CurrencyRate.rate_date >= start_date,
            CurrencyRate.rate_date <= end_date
        )
        results = session.execute(stmt).scalars().all()
        return results
    


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch currency data by code")

    parser.add_argument("currency_code", type=str, help="The currency code to fetch data for")

    parser.add_argument("start_date", type=str, help="Start date in YYYY-MM-DD format")

    parser.add_argument("end_date", type=str, help="End date in YYYY-MM-DD format")
    return parser.parse_args()

def main():
    args = parse_args()
    session = SessionLocal()
    columns = CurrencyRate.__table__.columns.keys()
    df = pd.DataFrame(columns=columns)

    if args.start_date and args.end_date:
        data = get_historical_currency_data(
            session,
            args.currency_code,
            args.start_date,
            args.end_date
        )

        df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
        
    else:
        data = get_all_currency_data(session, args.currency_code)

        df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
    
    df.set_index('rate_date', inplace=True)

    output_file = QUERIED_DATA_PATH / f"{args.currency_code}_data.csv"
    df.to_csv(output_file)