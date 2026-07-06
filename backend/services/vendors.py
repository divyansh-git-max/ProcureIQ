from core.seed_data import VENDORS
from db.session import get_pool, init_db_pool
from repositories.vendors import VendorRepository
from schemas.vendors import Vendor


async def list_vendors() -> list[Vendor]:
    try:
        await init_db_pool()
        async with get_pool().acquire() as conn:
            vendors = await VendorRepository(conn).list_all()
            if vendors:
                return vendors
    except Exception:
        pass
    return [Vendor.model_validate(vendor) for vendor in VENDORS]
