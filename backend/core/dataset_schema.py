from typing import Optional
from pydantic import BaseModel, Field

class Item(BaseModel):
    sku: str
    description: str
    qty: int
    unit_price: float
    total: float

class PurchaseOrder(BaseModel):
    id: str
    vendor_id: str
    items: list[Item]
    total: float
    currency: str = "INR"
    date: str
    status: str

class Clause(BaseModel):
    ref: str
    text: str
    penalty_pct: Optional[float] = None
    delivery_days: Optional[int] = None

class Contract(BaseModel):
    id: str
    vendor_id: str
    title: str
    clauses: list[Clause]
    effective_date: str

class Invoice(BaseModel):
    id: str
    po_id: str
    vendor_id: str
    items: list[Item]
    total: float
    invoice_date: str
    due_date: str

class GoodsReceiptNote(BaseModel):
    id: str
    po_id: str
    vendor_id: str
    received_date: str
    items: list[Item]  # What was actually received

class RiskHistory(BaseModel):
    week: str
    score: int

class VendorRecord(BaseModel):
    id: str
    name: str
    category: str
    risk_history: list[RiskHistory]
