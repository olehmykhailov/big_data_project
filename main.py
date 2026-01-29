import argparse
import sys
from datetime import date
from database.db import SessionLocal
from etl import (
    save_currencies,
    run_daily_etl,
    run_historical_etl,
    START_DATE,
    END_DATE
)
from database.db_query import run_query

def main():
    parser = argparse.ArgumentParser(description="Big Data Project CLI")
    subparsers = parser.add_subparsers(dest="main_command", required=True, help="Main command")

    # ==========================
    # ETL Command
    # ==========================
    etl_parser = subparsers.add_parser("etl", help="Run ETL processes")
    etl_subparsers = etl_parser.add_subparsers(dest="etl_command", required=True, help="ETL subcommand")

    # ETL: init
    init_parser = etl_subparsers.add_parser("init", help="Initialize static data (currencies)")
    init_parser.add_argument("--csv-path", default="currencies.csv", help="Path to currencies CSV")

    # ETL: daily
    daily_parser = etl_subparsers.add_parser("daily", help="Run daily ETL for latest data")
    daily_parser.add_argument("--csv-path", default="currencies.csv", help="Path to currencies CSV")
    daily_parser.add_argument("--skip-currencies", action="store_true", help="Skip downloading currency rates")
    daily_parser.add_argument("--skip-gold", action="store_true", help="Skip downloading gold prices")

    # ETL: history
    history_parser = etl_subparsers.add_parser("history", help="Run historical ETL")
    history_parser.add_argument("--start", type=date.fromisoformat, help="Start date (YYYY-MM-DD)")
    history_parser.add_argument("--end", type=date.fromisoformat, help="End date (YYYY-MM-DD)")
    history_parser.add_argument("--csv-path", default="currencies.csv", help="Path to currencies CSV")
    history_parser.add_argument("--skip-currencies", action="store_true", help="Skip downloading currency rates")
    history_parser.add_argument("--skip-gold", action="store_true", help="Skip downloading gold prices")

    # ==========================
    # Query Command
    # ==========================
    query_parser = subparsers.add_parser("query", help="Query database data")
    query_parser.add_argument("currency_code", type=str, help="The currency code to fetch data for")
    query_parser.add_argument("--start", type=str, help="Start date in YYYY-MM-DD format")
    query_parser.add_argument("--end", type=str, help="End date in YYYY-MM-DD format")

    args = parser.parse_args()

    # Dispatch Logic
    if args.main_command == "etl":
        session = SessionLocal()
        try:
            if args.etl_command == "init":
                save_currencies(session, args.csv_path)
                print("Database initialized with currencies.")

            elif args.etl_command == "daily":
                run_daily_etl(
                    session,
                    load_currencies=not args.skip_currencies,
                    load_gold=not args.skip_gold,
                    csv_path=args.csv_path
                )

            elif args.etl_command == "history":
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
            print(f"ETL Error: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            session.close()

    elif args.main_command == "query":
        run_query(args.currency_code, args.start, args.end)

if __name__ == "__main__":
    main()
