from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    UniqueConstraint,
    TIMESTAMP,
    func
)
from database.db import Base


class Currency(Base):
    __tablename__ = "currency"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    code = Column(String(5), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    table_type = Column(String(1), nullable=False)


class CurrencyRate(Base):
    __tablename__ = "currency_rate"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    currency_code = Column(String(5), nullable=False)
    rate_date = Column(Date, nullable=False)
    rate = Column(Numeric(19, 6), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "currency_code",
            "rate_date",
            name="uq_currency_rate_code_date",
        ),
    )


class GoldPrice(Base):
    __tablename__ = "gold_price"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    price_date = Column(Date, nullable=False, unique=True, index=True)
    price_pln = Column(Numeric(12, 4), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())