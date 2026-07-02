from app.core.seed_data import VENDORS
from app.db.session import get_pool, init_db_pool
from app.repositories.vendors import VendorRepository
from app.schemas.vendors import Vendor


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
