from fastapi import APIRouter, HTTPException
from typing import List

from routers.models import CompanySymbol
from services.company_symbol_service import CompanySymbolService
from utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("company_symbol_router", log_to_console=True)

class CompanySymbolRouter():
    """Router handling company symbol endpoints and WebSocket connections"""
    def __init__(self):
        self.service = CompanySymbolService(CompanySymbol)
        self.router = APIRouter(prefix="/company_symbol", tags=["company_symbol"])
        self.setup_routes()

    def setup_routes(self):
        """Configure API routes"""
        self.router.add_api_route(
            "/",
            self.get_company_symbol,
            methods=["GET"],
            response_model=List[CompanySymbol]
        )

    async def get_company_symbol(self) -> List[CompanySymbol]:
        """REST API endpoint to get company symbol"""
        try:
            company_symbols = self.service.get_company_symbol()

            if not company_symbols:
                raise HTTPException(
                    status_code=404,
                    detail=f"No company symbol found for the specified parameters"
                )

            return company_symbols

        except HTTPException:
            raise

        except Exception as e:
            logger.exception(f"Error in get_company_symbol: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while retrieving company symbol"
            )

company_symbol_router = CompanySymbolRouter().router


