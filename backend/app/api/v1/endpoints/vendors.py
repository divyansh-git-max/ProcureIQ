from fastapi import APIRouter

from app.schemas.vendors import Vendor
from app.services.vendors import list_vendors as fetch_vendors

router = APIRouter()


@router.get("", response_model=list[Vendor], response_model_by_alias=True)
async def list_vendors() -> list[Vendor]:
    """Return vendor risk intelligence and forecast summaries."""
    return await fetch_vendors()
