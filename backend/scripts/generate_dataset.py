import json
import os
from pathlib import Path

# The anomalies to generate:
# Vendor 1 (Northstar Steelworks): Invoice overcharges PO by 18.4% (PIQ-4821)
# Vendor 2 (Apex ReadyMix): Duplicate invoice submission (PIQ-4819)
# Vendor 3 (Kaveri Electricals): Late delivery, penalty clause missed (PIQ-4814)

def generate_vendors():
    return [
        {
            "id": "VEN-0042",
            "name": "Northstar Steelworks",
            "category": "Structural steel",
            "risk_history": [{"week": "W1", "score": 80}, {"week": "W2", "score": 84}]
        },
        {
            "id": "VEN-0107",
            "name": "Apex ReadyMix Pvt. Ltd.",
            "category": "Concrete",
            "risk_history": [{"week": "W1", "score": 60}, {"week": "W2", "score": 68}]
        },
        {
            "id": "VEN-0033",
            "name": "Kaveri Electricals",
            "category": "MEP supplies",
            "risk_history": [{"week": "W1", "score": 55}, {"week": "W2", "score": 52}]
        }
    ]

def generate_contracts():
    return [
        {
            "id": "CTR-2025-012",
            "vendor_id": "VEN-0042",
            "title": "Master Steel Supply Agreement",
            "clauses": [
                {"ref": "§4.2", "text": "Unit pricing for structural steel is fixed at ₹67,000/tonne for the duration of Q1 2026."}
            ],
            "effective_date": "2026-01-01"
        },
        {
            "id": "CTR-2025-045",
            "vendor_id": "VEN-0107",
            "title": "Concrete Supply Framework",
            "clauses": [
                {"ref": "§2.1", "text": "ReadyMix concrete supply at standard market rates."}
            ],
            "effective_date": "2026-01-15"
        },
        {
            "id": "CTR-2025-094",
            "vendor_id": "VEN-0033",
            "title": "MEP Electricals Contract",
            "clauses": [
                {"ref": "§8.7", "text": "Liquidated damages: A 0.5% weekly penalty applies for deliveries received after the agreed deadline.", "penalty_pct": 0.5, "delivery_days": 30}
            ],
            "effective_date": "2026-02-01"
        }
    ]

def generate_pos():
    return [
        {
            "id": "PO-88421",
            "vendor_id": "VEN-0042",
            "items": [
                {"sku": "STL-500", "description": "TMT Bars 500D", "qty": 150, "unit_price": 67000.0, "total": 10050000.0}
            ],
            "total": 10050000.0,
            "currency": "INR",
            "date": "2026-03-01",
            "status": "approved"
        },
        {
            "id": "PO-88430",
            "vendor_id": "VEN-0107",
            "items": [
                {"sku": "RMC-M30", "description": "ReadyMix Concrete M30", "qty": 200, "unit_price": 3600.0, "total": 720000.0}
            ],
            "total": 720000.0,
            "currency": "INR",
            "date": "2026-03-05",
            "status": "approved"
        },
        {
            "id": "PO-88450",
            "vendor_id": "VEN-0033",
            "items": [
                {"sku": "CBL-25", "description": "25mm Copper Cable (Roll)", "qty": 100, "unit_price": 2400.0, "total": 240000.0}
            ],
            "total": 240000.0,
            "currency": "INR",
            "date": "2026-03-10",
            "status": "approved"
        }
    ]

def generate_invoices():
    return [
        # PIQ-4821: Northstar overcharges by 18.4%
        # Rate billed at 79,200 instead of 67,000.
        # 150 * 79,200 = 11,880,000. (11,880,000 / 10,050,000 = 1.182 -> ~18.2% delta)
        {
            "id": "INV-2026-0187",
            "po_id": "PO-88421",
            "vendor_id": "VEN-0042",
            "items": [
                {"sku": "STL-500", "description": "TMT Bars 500D", "qty": 150, "unit_price": 79200.0, "total": 11880000.0}
            ],
            "total": 11880000.0,
            "invoice_date": "2026-03-15",
            "due_date": "2026-04-15"
        },
        # PIQ-4819: Apex Duplicate invoice 1
        {
            "id": "INV-2026-0194",
            "po_id": "PO-88430",
            "vendor_id": "VEN-0107",
            "items": [
                {"sku": "RMC-M30", "description": "ReadyMix Concrete M30", "qty": 200, "unit_price": 3600.0, "total": 720000.0}
            ],
            "total": 720000.0,
            "invoice_date": "2026-03-20",
            "due_date": "2026-04-20"
        },
        # PIQ-4819: Apex Duplicate invoice 2 (same PO, same items, different invoice ID)
        {
            "id": "INV-2026-0212",
            "po_id": "PO-88430",
            "vendor_id": "VEN-0107",
            "items": [
                {"sku": "RMC-M30", "description": "ReadyMix Concrete M30", "qty": 200, "unit_price": 3600.0, "total": 720000.0}
            ],
            "total": 720000.0,
            "invoice_date": "2026-03-22",
            "due_date": "2026-04-22"
        },
        # PIQ-4814: Kaveri Late delivery, penalty not applied
        # Agreed deadline was 30 days from 2026-03-10 = 2026-04-09.
        # Delivered on 2026-04-21 (12 days late).
        # Penalty should be 0.5% per week. Invoice doesn't have it.
        {
            "id": "INV-2026-0240",
            "po_id": "PO-88450",
            "vendor_id": "VEN-0033",
            "items": [
                {"sku": "CBL-25", "description": "25mm Copper Cable (Roll)", "qty": 100, "unit_price": 2400.0, "total": 240000.0}
            ],
            "total": 240000.0,
            "invoice_date": "2026-04-22",
            "due_date": "2026-05-22"
        }
    ]

def generate_grns():
    return [
        {
            "id": "GRN-33201",
            "po_id": "PO-88421",
            "vendor_id": "VEN-0042",
            "received_date": "2026-03-16",
            "items": [
                {"sku": "STL-500", "description": "TMT Bars 500D", "qty": 150, "unit_price": 67000.0, "total": 10050000.0}
            ]
        },
        {
            "id": "GRN-33205",
            "po_id": "PO-88430",
            "vendor_id": "VEN-0107",
            "received_date": "2026-03-21",
            "items": [
                {"sku": "RMC-M30", "description": "ReadyMix Concrete M30", "qty": 200, "unit_price": 3600.0, "total": 720000.0}
            ]
        },
        # PIQ-4814: Kaveri Late delivery GRN (12 days after 2026-04-09)
        {
            "id": "GRN-33219",
            "po_id": "PO-88450",
            "vendor_id": "VEN-0033",
            "received_date": "2026-04-21",
            "items": [
                {"sku": "CBL-25", "description": "25mm Copper Cable (Roll)", "qty": 100, "unit_price": 2400.0, "total": 240000.0}
            ]
        }
    ]

def main():
    data_dir = Path("f:/ProcureIQ-v0/procureIQ-v0/backend/data")
    data_dir.mkdir(parents=True, exist_ok=True)

    with open(data_dir / "vendors.json", "w") as f:
        json.dump(generate_vendors(), f, indent=2)

    with open(data_dir / "contracts.json", "w") as f:
        json.dump(generate_contracts(), f, indent=2)

    with open(data_dir / "pos.json", "w") as f:
        json.dump(generate_pos(), f, indent=2)

    with open(data_dir / "invoices.json", "w") as f:
        json.dump(generate_invoices(), f, indent=2)

    with open(data_dir / "grns.json", "w") as f:
        json.dump(generate_grns(), f, indent=2)
    
    print("Synthetic dataset generated in backend/data/")

if __name__ == "__main__":
    main()
