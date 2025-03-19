from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.stock_summary_router import stock_summary_router
from routers.latest_price_router import latest_price_router
from routers.company_symbols_router import company_symbol_router
from routers.stock_price_1s_router import stock_price_1s_router

# Create an instance of the router
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock_summary_router)
app.include_router(latest_price_router)
app.include_router(company_symbol_router)
app.include_router(stock_price_1s_router)
