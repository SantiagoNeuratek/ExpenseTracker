from fastapi import APIRouter

from app.api.v1.endpoints import auth, companies, categories, expenses, apikeys, monitoring, audit

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(apikeys.router, prefix="/apikeys", tags=["apikeys"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])