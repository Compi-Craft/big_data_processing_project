from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import pandas as pd
from app.models import SymbolStatsLastHour, HistoricalTrades
from app.database import get_db
from datetime import datetime, timedelta
from cassandra.cluster import Cluster
from zoneinfo import ZoneInfo
from collections import defaultdict

router = APIRouter()

cluster = Cluster(["cassandra"])
session = cluster.connect()

def rows_to_responce(rows):
    df = pd.DataFrame(rows)
    response = df.to_dict(orient="records")

    return response

@router.get("/health")
def get_health_status():
    return {"status": 200}

@router.get("/transactions_count_last_6_hours")
def transactions_count_last_6_hours(db: Session = Depends(get_db)):
    now = datetime.now(ZoneInfo("Europe/Kyiv")).replace(minute=0, second=0, microsecond=0).replace(tzinfo=None)
    end_time = now
    start_time = end_time - timedelta(hours=6)

    # Агрегуємо загальну кількість транзакцій за 6 годин для кожного символу
    results = db.query(
        SymbolStatsLastHour.symbol,
        func.sum(SymbolStatsLastHour.transaction_count).label("total_transaction_count")
    ).filter(
        SymbolStatsLastHour.hour_start >= start_time,
        SymbolStatsLastHour.hour_start < end_time
    ).group_by(
        SymbolStatsLastHour.symbol
    ).order_by(
        SymbolStatsLastHour.symbol
    ).all()

    # Повертаємо загальну суму для кожного символу
    data = {}
    for row in results:
        data[row.symbol] = {
            "total_transaction_count": int(row.total_transaction_count) if row.total_transaction_count else 0
        }

    return {"count": data}

@router.get("/trade_volume_last_6_hours")
def trade_volume_last_6_hours(db: Session = Depends(get_db)):
    now = datetime.now(ZoneInfo("Europe/Kyiv")).replace(minute=0, second=0, microsecond=0).replace(tzinfo=None)
    end_time = now
    start_time = end_time - timedelta(hours=6)

    # Агрегуємо загальний обсяг торгівлі за 6 годин для кожного символу
    results = db.query(
        SymbolStatsLastHour.symbol,
        func.sum(SymbolStatsLastHour.total_trade_volume).label("total_volume")
    ).filter(
        SymbolStatsLastHour.hour_start >= start_time,
        SymbolStatsLastHour.hour_start < end_time
    ).group_by(
        SymbolStatsLastHour.symbol
    ).order_by(
        SymbolStatsLastHour.symbol
    ).all()

    # Повертаємо загальну суму для кожного символу
    data = {}
    for row in results:
        data[row.symbol] = {
            "total_trade_volume": float(row.total_volume) if row.total_volume else 0.0
        }

    return {"count": data}

@router.get("/hourly_stats_last_12_hours")
def hourly_stats_last_12_hours(db: Session = Depends(get_db)):
    now = datetime.now(ZoneInfo("Europe/Kyiv")).replace(minute=0, second=0, microsecond=0).replace(tzinfo=None)
    end_time = now
    start_time = end_time - timedelta(hours=12)

    rows = db.query(
        SymbolStatsLastHour.symbol,
        SymbolStatsLastHour.hour_start,
        SymbolStatsLastHour.transaction_count,
        SymbolStatsLastHour.total_trade_volume
    ).filter(
        SymbolStatsLastHour.hour_start >= start_time,
        SymbolStatsLastHour.hour_start < end_time
    ).order_by(
        SymbolStatsLastHour.symbol,
        SymbolStatsLastHour.hour_start
    ).all()

    stats = defaultdict(list)
    for row in rows:
        stats[row.symbol].append({
            "hour_start": row.hour_start.isoformat(),
            "transaction_count": row.transaction_count,
            "total_trade_volume": row.total_trade_volume
        })

    return {"stats": stats}

@router.get("/transactions_in_last_n_min")
def get_transactions_count(symbol: str, n_minutes: int, db: Session = Depends(get_db)):
    now = datetime.now(ZoneInfo("Europe/Kyiv")).replace(second=0, microsecond=0).replace(tzinfo=None)
    start_time = now - timedelta(minutes=n_minutes)
    end_time = now

    num_trades = db.query(HistoricalTrades).filter(
        HistoricalTrades.symbol == symbol,
        HistoricalTrades.currenttimestamp >= start_time,
        HistoricalTrades.currenttimestamp < end_time
    ).count()

    return {"symbol": symbol, "number_of_trades": num_trades}

@router.get("/top_n_highest_volumes")
def get_top_n_highest_volumes(top_n: int, db: Session = Depends(get_db)):
    now = datetime.now(ZoneInfo("Europe/Kyiv"))
    start_time = now - timedelta(hours=1)

    results = (
        db.query(
            HistoricalTrades.symbol,
            func.sum(HistoricalTrades.trade_volume).label("total_volume")
        )
        .filter(HistoricalTrades.currenttimestamp >= start_time)
        .group_by(HistoricalTrades.symbol)
        .order_by(desc("total_volume"))
        .limit(top_n)
        .all()
    )

    return {"top_symbols": [{"symbol": r.symbol, "total_volume": r.total_volume} for r in results]}

@router.get("/current_price")
def get_current_price(symbol: str):
    query = f"""
        SELECT *
        FROM orders.current_price
        WHERE symbol = '{symbol}'
    """

    rows = session.execute(query)
    df = pd.DataFrame(rows)
    sellprice = df["sellprice"].iloc[0]
    buyprice = df["buyprice"].iloc[0]

    return {"Symbol": symbol, "Sell price": sellprice, "Buy price": buyprice}
