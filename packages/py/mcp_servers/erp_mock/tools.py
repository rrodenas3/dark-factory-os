"""Specification-only declarations for the ERP mock MCP tools.

These functions document the tool contracts required by the Phase 3 manifest. Executable mock adapters should keep the
same names, schemas, mock data shapes, and risk metadata when implemented in the MCP server runtime.
"""

from __future__ import annotations


def get_invoice(invoice_id: str) -> None:
    """Fetch invoice details from the mock ERP.

    Risk tier:
        read_only

    Input schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "invoice_id": {
              "type": "string",
              "minLength": 1,
              "description": "ERP invoice identifier, for example INV-1001."
            }
          },
          "required": ["invoice_id"]
        }

    Output schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "invoice_id": {"type": "string"},
            "vendor_id": {"type": "string"},
            "vendor_name": {"type": "string"},
            "po_id": {"type": ["string", "null"]},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string", "enum": ["received", "matched", "exception", "paid", "void"]},
            "line_items": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "sku": {"type": "string"},
                  "description": {"type": "string"},
                  "quantity": {"type": "number"},
                  "unit_price": {"type": "number"},
                  "total": {"type": "number"}
                },
                "required": ["sku", "description", "quantity", "unit_price", "total"]
              }
            },
            "exception_codes": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["invoice_id", "vendor_id", "vendor_name", "amount", "currency", "status", "line_items"]
        }

    Mock data shape:
        {
          "invoice_id": "INV-1001",
          "vendor_id": "VEN-42",
          "vendor_name": "Acme Industrial Supply",
          "po_id": "PO-7001",
          "amount": 1842.50,
          "currency": "USD",
          "status": "exception",
          "line_items": [{"sku": "MRO-1", "description": "Safety gloves", "quantity": 100, "unit_price": 8.5,
          "total": 850.0}],
          "exception_codes": ["AMOUNT_MISMATCH"]
        }
    """
    raise NotImplementedError("Specification only; executable adapters must implement this MCP tool.")


def get_purchase_order(po_id: str) -> None:
    """Fetch purchase order details from the mock ERP.

    Risk tier:
        read_only

    Input schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "po_id": {
              "type": "string",
              "minLength": 1,
              "description": "ERP purchase order identifier, for example PO-7001."
            }
          },
          "required": ["po_id"]
        }

    Output schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "po_id": {"type": "string"},
            "vendor_id": {"type": "string"},
            "status": {"type": "string", "enum": ["open", "partially_received", "closed", "cancelled"]},
            "approved_amount": {"type": "number"},
            "currency": {"type": "string"},
            "received_amount": {"type": "number"},
            "line_items": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "sku": {"type": "string"},
                  "quantity_ordered": {"type": "number"},
                  "quantity_received": {"type": "number"},
                  "unit_price": {"type": "number"}
                },
                "required": ["sku", "quantity_ordered", "quantity_received", "unit_price"]
              }
            }
          },
          "required": ["po_id", "vendor_id", "status", "approved_amount", "currency", "line_items"]
        }

    Mock data shape:
        {
          "po_id": "PO-7001",
          "vendor_id": "VEN-42",
          "status": "partially_received",
          "approved_amount": 1800.00,
          "currency": "USD",
          "received_amount": 1760.00,
          "line_items": [{"sku": "MRO-1", "quantity_ordered": 100, "quantity_received": 100,
          "unit_price": 8.5}]
        }
    """
    raise NotImplementedError("Specification only; executable adapters must implement this MCP tool.")


def post_payment(invoice_id: str, amount: float, currency: str) -> None:
    """Post a payment against an approved invoice.

    Risk tier:
        financial

    Approval policy:
        Requires finance-manager approval when `amount` exceeds the configured threshold in
        `packages/py/governance/risk_registry.yaml`.

    Input schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "invoice_id": {"type": "string", "minLength": 1},
            "amount": {"type": "number", "exclusiveMinimum": 0},
            "currency": {"type": "string", "pattern": "^[A-Z]{3}$"}
          },
          "required": ["invoice_id", "amount", "currency"]
        }

    Output schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "payment_id": {"type": "string"},
            "invoice_id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string", "enum": ["posted", "queued_for_approval", "rejected"]},
            "posted_at": {"type": "string", "format": "date-time"}
          },
          "required": ["payment_id", "invoice_id", "amount", "currency", "status"]
        }

    Mock data shape:
        {
          "payment_id": "PAY-9001",
          "invoice_id": "INV-1001",
          "amount": 1842.50,
          "currency": "USD",
          "status": "queued_for_approval",
          "posted_at": "2026-06-19T12:00:00Z"
        }
    """
    raise NotImplementedError("Specification only; executable adapters must implement this MCP tool.")


def void_invoice(invoice_id: str, reason: str) -> None:
    """Void an invoice in the mock ERP.

    Risk tier:
        destructive

    Approval policy:
        Always requires an ActionReadinessPack and finance-director approval before execution.

    Input schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "invoice_id": {"type": "string", "minLength": 1},
            "reason": {"type": "string", "minLength": 10}
          },
          "required": ["invoice_id", "reason"]
        }

    Output schema:
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "invoice_id": {"type": "string"},
            "status": {"type": "string", "const": "void"},
            "voided_at": {"type": "string", "format": "date-time"},
            "reason": {"type": "string"},
            "audit_event_id": {"type": "string"}
          },
          "required": ["invoice_id", "status", "voided_at", "reason", "audit_event_id"]
        }

    Mock data shape:
        {
          "invoice_id": "INV-1001",
          "status": "void",
          "voided_at": "2026-06-19T12:05:00Z",
          "reason": "Duplicate invoice confirmed against INV-0998.",
          "audit_event_id": "AUD-3001"
        }
    """
    raise NotImplementedError("Specification only; executable adapters must implement this MCP tool.")
