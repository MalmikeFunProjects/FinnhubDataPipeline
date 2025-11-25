from pydantic import BaseModel


class LatestPrice(BaseModel):
    event_timestamp: int
    symbol: str
    last_price: float

    class Config:
        from_attributes = True
