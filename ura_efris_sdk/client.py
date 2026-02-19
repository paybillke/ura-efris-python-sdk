from typing import Dict, Any, Optional, List
from .base_client import BaseClient
from .validator import Validator
from .schemas import SCHEMAS
from .key_client import KeyClient

class Client(BaseClient):
    """
    High-level EFRIS client with business methods.
    Follows eTIMS-style: one method per interface, with validation.
    """
    
    def __init__(self, config: Dict[str, Any], key_client: "KeyClient"):
        super().__init__(config, key_client)
        self.validator = Validator()
    
    def _validate(self, data: Dict[str, Any], schema_key: str) -> Dict[str, Any]:
        """Internal: validate + serialize payload"""
        return self.validator.validate(data, schema_key)
    
    # =========================================================
    # SYSTEM SETUP & TEST (URA v1.5, page 3-4)
    # =========================================================
    
    def test_interface(self, data: Optional[Dict] = None) -> Dict[str, Any]:
        """T101: Test Interface - Verify connection + time sync (±10 min tolerance)"""
        return self._send("test_interface", data or {}, encrypt=False)
    
    def get_symmetric_key(self, force: bool = False) -> Dict[str, Any]:
        """T104: Get Symmetric Key - Fetch AES key (valid 24h)"""
        self.key_client.fetch_aes_key(force=force)
        return {"resultCd": "000", "resultMsg": "AES key refreshed"}
    
    def update_system_dictionary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T115: System Dictionary Update - Sync taxpayer dictionary with EFRIS"""
        return self.post("system_dictionary", data)
    
    # =========================================================
    # INVOICE MANAGEMENT ⭐ Most Critical (URA v1.5, page 9)
    # =========================================================
    
    def fiscalise_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        T109: Billing Upload - Fiscalise a single invoice/receipt.
        
        Args:
            data: Dict matching T109BillingUpload schema
            
        Returns:
            Response with fiscal data: FDN, verification code, QR code, etc.
        """
        validated = self._validate(data, "billing_upload")
        return self.post("billing_upload", validated)
    
    def fiscalise_batch_invoices(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T129: Batch Invoice Upload - Fiscalise multiple invoices in one call"""
        return self.post("batch_invoice_upload", data)
    
    def verify_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T108: Invoice Details - Validate a fiscalised invoice by FDN"""
        validated = self._validate(data, "invoice_details")
        return self.post("invoice_details", validated)
    
    def query_invoices(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T107: Invoice/Receipt Query - Search fiscalised transactions with filters"""
        validated = self._validate(data, "invoice_query")
        return self.post("invoice_query", validated)
    
    def check_taxpayer_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T137: Check Taxpayer Type - Verify VAT exemption/deeming status"""
        return self.post("check_taxpayer_type", data)
    
    # =========================================================
    # CREDIT/DEBIT NOTES (B2B/B2G Only - URA v1.5, page 9-10)
    # =========================================================
    
    def apply_credit_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T110: Credit Application - Request credit note (requires URA approval)"""
        validated = self._validate(data, "credit_application")
        return self.post("credit_application", validated)
    
    def query_credit_note_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T111: Credit Note Application Status Query"""
        return self.post("credit_note_status", data)
    
    def cancel_credit_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T114: Credit Note Application Cancel (for approved notes)"""
        return self.post("credit_note_cancel", data)
    
    def query_credit_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T118: Query Credit Note Application Details (for pending notes)"""
        return self.post("query_credit_application", data)
    
    def get_credit_application_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T113: Credit Note Application Detail"""
        return self.post("credit_application_detail", data)
    
    # =========================================================
    # REGISTRATION & MASTER DATA (URA v1.5, page 7)
    # =========================================================
    
    def query_taxpayer_by_tin(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T119: Query Taxpayer Information By TIN"""
        validated = self._validate(data, "query_taxpayer")
        return self.post("query_taxpayer", validated)
    
    def get_registered_branches(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T138: Get All Branches"""
        return self.post("get_branches", data)
    
    # =========================================================
    # STOCK & ITEM MANAGEMENT (URA v1.5, page 7-8)
    # =========================================================
    
    def query_commodity_categories(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T124: Query Commodity Category Pagination"""
        return self.post("query_commodity_category", data)
    
    def query_excise_duty_codes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T125: Query Excise Duty Codes (for excisable products)"""
        return self.post("query_excise_duty", data)
    
    def get_exchange_rates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T126: Get All Exchange Rates (for foreign currency invoicing)"""
        return self.post("get_exchange_rates", data)
    
    def upload_goods(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T130: Goods Upload - Register products on EFRIS"""
        validated = self._validate(data, "goods_upload")
        return self.post("goods_upload", validated)
    
    def inquire_goods(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T127: Goods/Services Inquiry - Search registered products"""
        return self.post("goods_inquiry", data)
    
    def query_goods_by_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T144: Query Goods by Code"""
        return self.post("query_goods_by_code", data)
    
    def query_stock_quantity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T128: Query Stock Quantity by Goods ID"""
        return self.post("query_stock", data)
    
    def maintain_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T131: Goods Stock Maintain - Update stock levels (in/out/adjustment)"""
        validated = self._validate(data, "stock_maintain")
        return self.post("stock_maintain", validated)
    
    def transfer_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T139: Goods Stock Transfer - Transfer between branches"""
        return self.post("stock_transfer", data)