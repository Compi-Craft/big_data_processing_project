from pydantic import BaseModel
from datetime import datetime

class StatsBySymbol(BaseModel):
    symbol: str
    transaction_count: int = 0
    total_trade_volume: float = 0.0

class StatsBySymbolAndHour(BaseModel):
    symbol: str
    hour_start: datetime
    transaction_count: int = 0
    total_trade_volume: float = 0.0