import logging
from fastapi import APIRouter, HTTPException
from typing import List

from routers.models import CompanySymbol
from services.company_symbol_service import CompanySymbolService

logging.basicConfig(level=logging.INFO)

class CompanySymbolRouter():
    def __init__(self):
        self.company_symbol_service = CompanySymbolService(CompanySymbol)
        self.router = APIRouter(prefix="/company_symbol", tags=["company_symbol"])
        self.setup_routes()

    def setup_routes(self):
        #HTTP routes
        self.router.add_api_route("/", self.get_company_symbol, methods=["GET"], response_model=List[CompanySymbol])


    async def get_company_symbol(self) -> List[CompanySymbol]:
        company_symbol = self.company_symbol_service.get_company_symbols()
        if not company_symbol:
            raise HTTPException(status_code=404, detail=f"Stock summary not found")
        return company_symbol

company_symbol_router = CompanySymbolRouter().router

