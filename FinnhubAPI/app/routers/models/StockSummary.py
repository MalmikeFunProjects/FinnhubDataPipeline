from  pydantic import BaseModel

class StockSummary(BaseModel):
    event_timestamp: int
    total_price: float
    symbols: list[str]
    symbol_prices: list[float]

    class Config:
        from_attributes = True
