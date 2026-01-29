from etl import run_daily_etl, run_historical_etl, save_currencies
from database.db import SessionLocal
import os
from datetime import date

def lambda_handler(event, context):
    session = SessionLocal()
    
    mode = event.get("mode", "daily")
    targets = event.get("target", "currencies,gold").split(",")
    csv_path = event.get("csv", "currencies.csv")
    
    load_currencies = "currencies" in targets
    load_gold = "gold" in targets

    try:
        if event.get("currencies_data"):
            save_currencies(session, csv_path=csv_path)

        if mode == "historical":
            start_str = event.get("start_date")
            end_str = event.get("end_date")
            start_date = date.fromisoformat(start_str) if start_str else None
            end_date = date.fromisoformat(end_str) if end_str else None

            if not start_date or not end_date:
                return {"statusCode": 400, "body": "start_date and end_date are required for historical mode (YYYY-MM-DD)"}

            run_historical_etl(
                session=session,
                csv_path=csv_path,
                start_date=start_date, 
                end_date=end_date,
                load_currencies=load_currencies,
                load_gold=load_gold
            )
        else:
            run_daily_etl(
                session=session,
                load_currencies=load_currencies,
                load_gold=load_gold,
                csv_path=csv_path
            )
            
        return {"statusCode": 200, "body": "ETL Finished Successfully"}
        
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
    finally:
        session.close()