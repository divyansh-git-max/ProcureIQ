from fastapi import APIRouter

from app.api.v1.endpoints import dashboard, documents, findings, operations, vendors

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(findings.router, prefix="/findings", tags=["findings"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])

