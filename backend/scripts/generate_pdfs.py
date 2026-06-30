import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Create PDF for the 3 scenarios:
# 1. PIQ-4821: Northstar Invoice (Overcharged rate)
# 2. PIQ-4819: Apex Invoices (Duplicates)
# 3. PIQ-4814: Kaveri Invoice (Late delivery, no penalty)

def create_invoice_pdf(filename, vendor_name, invoice_id, po_id, date, due_date, items, total):
    path = Path("f:/ProcureIQ-v0/procureIQ-v0/backend/data/documents") / filename
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Header
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("<b>TAX INVOICE</b>", title_style))
    
    elements.append(Paragraph(f"<b>Vendor:</b> {vendor_name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Invoice ID:</b> {invoice_id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Purchase Order Ref:</b> {po_id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {date}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Due Date:</b> {due_date}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [["SKU", "Description", "Qty", "Unit Price (INR)", "Total (INR)"]]
    for item in items:
        data.append([
            item["sku"], 
            item["description"], 
            str(item["qty"]), 
            f"{item['unit_price']:,.2f}", 
            f"{item['total']:,.2f}"
        ])
    data.append(["", "", "", "<b>GRAND TOTAL</b>", f"<b>{total:,.2f}</b>"])
    
    t = Table(data, colWidths=[80, 200, 50, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    doc.build(elements)
    print(f"Generated {filename}")

def main():
    # 1. Northstar Invoice (Overcharged)
    create_invoice_pdf(
        "Northstar_Invoice_0187.pdf",
        "Northstar Steelworks",
        "INV-2026-0187",
        "PO-88421",
        "2026-03-15",
        "2026-04-15",
        [{"sku": "STL-500", "description": "TMT Bars 500D", "qty": 150, "unit_price": 79200.0, "total": 11880000.0}],
        11880000.0
    )
    
    # 2. Apex Duplicate Invoices
    create_invoice_pdf(
        "Apex_Invoice_0194.pdf",
        "Apex ReadyMix Pvt. Ltd.",
        "INV-2026-0194",
        "PO-88430",
        "2026-03-20",
        "2026-04-20",
        [{"sku": "RMC-M30", "description": "ReadyMix Concrete M30", "qty": 200, "unit_price": 3600.0, "total": 720000.0}],
        720000.0
    )
    create_invoice_pdf(
        "Apex_Invoice_0212.pdf",
        "Apex ReadyMix Pvt. Ltd.",
        "INV-2026-0212", # Different invoice ID, same everything else
        "PO-88430",
        "2026-03-22",
        "2026-04-22",
        [{"sku": "RMC-M30", "description": "ReadyMix Concrete M30", "qty": 200, "unit_price": 3600.0, "total": 720000.0}],
        720000.0
    )
    
    # 3. Kaveri Invoice (Late delivery, missing penalty)
    create_invoice_pdf(
        "Kaveri_Invoice_0240.pdf",
        "Kaveri Electricals",
        "INV-2026-0240",
        "PO-88450",
        "2026-04-22",
        "2026-05-22",
        [{"sku": "CBL-25", "description": "25mm Copper Cable (Roll)", "qty": 100, "unit_price": 2400.0, "total": 240000.0}],
        240000.0 # Notice no deduction line item for penalty
    )

if __name__ == "__main__":
    main()
