from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

def default_hour_start():
    now = datetime.utcnow()
    return now.replace(minute=0, second=0, microsecond=0)

class SymbolStatsLastHour(Base):
    __tablename__ = "symbol_stats_last_hour"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    transaction_count = Column(BigInteger, nullable=False)
    total_trade_volume = Column(Float, nullable=False)
    hour_start = Column(DateTime, nullable=False, default=default_hour_start)

class HistoricalTrades(Base):
    __tablename__ = "historical_trades"

    trade_id = Column(String, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    trade_volume = Column(Float, nullable=False)
    currenttimestamp = Column(DateTime, nullable=False)

    