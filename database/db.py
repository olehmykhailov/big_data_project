import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    os.getenv("DATABASE_URL"),
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine)
