from pydantic import BaseModel


class CompanySymbol(BaseModel):
    symbol: str

    class Config:
        from_attributes = True
