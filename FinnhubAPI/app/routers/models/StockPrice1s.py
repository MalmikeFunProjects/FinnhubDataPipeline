from pydantic import BaseModel

class StockPrice1s(BaseModel):
    event_timestamp: int
    symbol: str
    count: int
    avg_price: float

    class Config:
        from_attributes = True
