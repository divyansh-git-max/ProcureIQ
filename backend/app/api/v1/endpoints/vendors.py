from fastapi import APIRouter

from app.schemas.vendors import Vendor

router = APIRouter()


@router.get("", response_model=list[Vendor])
async def list_vendors() -> list[Vendor]:
    """Return vendor risk intelligence and forecast summaries."""
    return []

