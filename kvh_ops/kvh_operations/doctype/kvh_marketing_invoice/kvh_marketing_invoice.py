import frappe
import secrets
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_url


class KVHMarketingInvoice(Document):
    """
    Marketing Invoice for KVH Marketing module.

    Mirrors: marketing_invoices, marketing_invoice_items, marketing_invoice_payments tables.
    Key business logic:
    - Auto-recalculate totals when items or payments change (recalc_marketing_invoice trigger)
    - Status auto-updates: Paid if amount_paid >= total, Partially Paid if > 0, else Sent
    - Public URL via token (marketing-invoice.$token route)
    - GST calculation: (subtotal - discount) * tax_percent / 100
    """

    def before_insert(self):
        self._generate_invoice_number()
        self._generate_token()

    def validate(self):
        self._recalculate()
        self._set_public_url()

    def _generate_invoice_number(self):
        if self.invoice_number:
            return
        from kvh_ops.utils.naming import next_fy_id, PREFIX_MKT_INVOICE
        self.invoice_number = next_fy_id(PREFIX_MKT_INVOICE)

    def _generate_token(self):
        """Generate a unique token for the public invoice URL."""
        if self.token:
            return
        self.token = secrets.token_urlsafe(32)

    def _set_public_url(self):
        """Build public URL from token."""
        if self.token:
            base = get_url()
            self.public_url = f"{base}/mkt-invoice/{self.token}"

    def _recalculate(self):
        """
        Recalculate all invoice totals.
        Mirrors: recalc_marketing_invoice trigger (PostgreSQL).

        Formula:
          subtotal = sum of item amounts
          tax_amount = (subtotal - discount) * tax_percent / 100
          total = (subtotal - discount) + tax_amount
          amount_paid = sum of payments
          balance = max(total - amount_paid, 0)
          status auto-updates (if not Cancelled or Draft)
        """
        # Sum items
        subtotal = sum(flt(item.amount) for item in (self.invoice_items or []))

        # Compute items amount from qty * unit_price
        for item in self.invoice_items or []:
            if not item.amount:
                item.amount = flt(item.quantity) * flt(item.unit_price)
        subtotal = sum(flt(item.amount) for item in (self.invoice_items or []))

        # Sum payments
        amount_paid = sum(flt(p.amount) for p in (self.payments or []))

        # Compute tax
        discount = flt(self.discount)
        tax_percent = flt(self.tax_percent) or 18.0
        taxable = max(subtotal - discount, 0)
        tax_amount = flt(taxable * tax_percent / 100, 2)
        total = flt(taxable + tax_amount, 2)
        balance = max(total - amount_paid, 0)

        self.subtotal = flt(subtotal, 2)
        self.tax_amount = tax_amount
        self.total = total
        self.amount_paid = flt(amount_paid, 2)
        self.balance = flt(balance, 2)

        # Auto-update status (unless Cancelled or Draft)
        if self.status not in ("Cancelled", "Draft"):
            if amount_paid >= total and total > 0:
                self.status = "Paid"
            elif amount_paid > 0:
                self.status = "Partially Paid"
            else:
                self.status = "Sent"


@frappe.whitelist()
def get_invoice_by_token(token):
    """
    Retrieve marketing invoice by public token (no authentication required).
    Mirrors: marketing-invoice.$token public route in Lovable.
    """
    invoice_name = frappe.db.get_value("KVH Marketing Invoice", {"token": token}, "name")
    if not invoice_name:
        frappe.throw(_("Invoice not found."), frappe.DoesNotExistError)

    invoice = frappe.get_doc("KVH Marketing Invoice", invoice_name)
    # Return safe public fields only
    return {
        "invoice_number": invoice.invoice_number,
        "client_name": invoice.client_name_display,
        "invoice_date": str(invoice.invoice_date),
        "due_date": str(invoice.due_date) if invoice.due_date else None,
        "period_from": str(invoice.period_from) if invoice.period_from else None,
        "period_to": str(invoice.period_to) if invoice.period_to else None,
        "status": invoice.status,
        "currency": invoice.currency,
        "subtotal": invoice.subtotal,
        "discount": invoice.discount,
        "tax_percent": invoice.tax_percent,
        "tax_amount": invoice.tax_amount,
        "total": invoice.total,
        "amount_paid": invoice.amount_paid,
        "balance": invoice.balance,
        "notes": invoice.notes,
        "terms": invoice.terms,
        "items": [
            {
                "kind": item.kind,
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
            }
            for item in (invoice.invoice_items or [])
        ],
    }
