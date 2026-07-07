import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import init_db_pool, get_pool
from repositories.vendors import VendorRepository
from ingestion.doc_intel import detect_vendor

async def main():
    await init_db_pool()
    text = """
        Dear Sir, Please find enclosed our billing statement for structural steel
        supply delivered to Site B, Pune. Total payable: INR 14,50,000.
        Regards, Mehta Steel Works Pvt. Ltd.
        """
    async with get_pool().acquire() as conn:
        repo = VendorRepository(conn)
        vendor_id, vendor_name = await detect_vendor(text, repo)
        print("Vendor returned:", vendor_name)
        
        vendors = await repo.list_all()
        for v in vendors:
            print("Checking vendor:", v.name)
            if v.name.lower() in text.lower():
                print("  -> exact match!")
            tokens = text[:500].split()
            import difflib
            for token in tokens:
                if len(token) < 4: continue
                matches = difflib.get_close_matches(token, [v.name], n=1, cutoff=0.8)
                if matches:
                    print("  -> fuzzy match on token:", token)

asyncio.run(main())
