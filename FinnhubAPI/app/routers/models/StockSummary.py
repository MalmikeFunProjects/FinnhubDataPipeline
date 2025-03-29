from  pydantic import BaseModel

class StockSummary(BaseModel):
    event_timestamp: int
    total_price: float
    symbol_prices: dict[str, float]

    class Config:
        from_attributes = True
