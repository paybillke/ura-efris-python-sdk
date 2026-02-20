"""
EFRIS Client
Main client class with business logic methods for all EFRIS operations.
Extends BaseClient with validated methods for each API interface.
"""
from typing import Dict, Any, Optional, List, Union
from .base_client import BaseClient
from .validator import Validator
from .schemas import SCHEMAS
from .key_client import KeyClient


class Client(BaseClient):
    """
    Main EFRIS API client with business logic methods.
    
    Provides validated methods for:
        - Authentication (sign_in, get_symmetric_key)
        - Invoice operations (upload, query, verify)
        - Credit/Debit note operations
        - Goods and stock management
        - System queries (dictionary, exchange rates, etc.)
    
    Example:
        config = load_config_from_env()
        key_client = KeyClient(...)
        client = Client(config, key_client)
        client.sign_in()
        client.fiscalise_invoice(invoice_data)
    """
    
    def __init__(self, config: Dict[str, Any], key_client: "KeyClient"):
        """
        Initialize client with configuration and key manager.
        
        Args:
            config: Configuration dictionary
            key_client: KeyClient instance
        """
        super().__init__(config, key_client)
        self.validator = Validator()
    
    def _validate(self, data: Dict[str, Any], schema_key: str) -> Dict[str, Any]:
        """
        Validate data against Pydantic schema.
        
        Args:
            data: Data to validate
            schema_key: Schema name from SCHEMAS dict
        
        Returns:
            dict: Validated data
        
        Raises:
            ValidationException: If validation fails
        """
        return self.validator.validate(data, schema_key)
    
    # =========================================================================
    # AUTHENTICATION & INITIALIZATION
    # =========================================================================
    
    def test_interface(self, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Test API connectivity (T101 - Get Server Time).
        
        Args:
            data: Optional request data
        
        Returns:
            dict: Response with currentTime field
        """
        raw_resp = self._send("test_interface", data or {}, encrypt=False)
        # Handle potential encrypted response
        if "data" in raw_resp and "content" in raw_resp["data"]:
            import base64, json
            try:
                content_b64 = raw_resp["data"]["content"]
                if content_b64:
                    decoded = base64.b64decode(content_b64).decode('utf-8')
                    raw_resp["data"]["content"] = json.loads(decoded)
            except Exception:
                pass
        return raw_resp
    
    def client_init(self) -> Dict[str, Any]:
        """
        Initialize client (T102 - Client Initialization).
        Note: This implementation uses local PFX, not T102 Whitebox keys.
        
        Returns:
            dict: Initialization response
        """
        return self._send("client_init", {}, encrypt=False)
    
    def sign_in(self) -> Dict[str, Any]:
        """
        Sign in to EFRIS (T103 - Login).
        Retrieves taxpayer and device information.
        
        Returns:
            dict: Login response with taxpayer/device details
        
        Note: API docs say T103 response is encrypted, but this
        implementation sends encrypt=False. May need adjustment.
        """
        return self._send("sign_in", {}, encrypt=False)
    
    def get_symmetric_key(self, force: bool = False) -> Dict[str, Any]:
        """
        Fetch AES symmetric key (T104).
        
        Args:
            force: Force key refresh
        
        Returns:
            dict: Status message
        """
        self.key_client.fetch_aes_key(force=force)
        return {"resultCd": "000", "resultMsg": "AES key refreshed"}
    
    def forget_password(self, user_name: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password (T105).
        
        Args:
            user_name: Username
            new_password: New password
        
        Returns:
            dict: API response
        """
        payload = {"userName": user_name, "changedPassword": new_password}
        return self._send("forget_password", payload, encrypt=True)
    
    def update_system_dictionary(self, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Update system dictionary (T115).
        Retrieves tax rates, currencies, payment methods, etc.
        
        Args:
            data: Optional request data
        
        Returns:
            dict: Dictionary data
        """
        return self.post("system_dictionary", data or {}, encrypt=False)
    
    # =========================================================================
    # INVOICE OPERATIONS
    # =========================================================================
    
    def fiscalise_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload invoice to EFRIS (T109 - Billing Upload).
        
        Args:
            data: Invoice data (validated against T109 schema)
        
        Returns:
            dict: API response with invoice details
        
        Raises:
            ValidationException: If invoice data is invalid
        """
        validated = self._validate(data, "billing_upload")
        return self.post("billing_upload", validated, encrypt=True)
    
    def fiscalise_batch_invoices(self, invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload multiple invoices in batch (T129).
        
        Args:
            invoices: List of invoice objects with invoiceContent and invoiceSignature
        
        Returns:
            dict: Batch upload results
        """
        payload = [
            {
                "invoiceContent": inv.get("invoiceContent", ""),
                "invoiceSignature": inv.get("invoiceSignature", "")
            }
            for inv in invoices
        ]
        return self.post("batch_invoice_upload", payload, encrypt=True)
    
    def verify_invoice(self, invoice_no: str) -> Dict[str, Any]:
        """
        Get invoice details (T108).
        
        Args:
            invoice_no: Invoice number to verify
        
        Returns:
            dict: Invoice details
        """
        validated = self._validate({"invoiceNo": invoice_no}, "invoice_details")
        return self.post("invoice_details", validated, encrypt=True)
    
    def query_invoices(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query normal invoices (T107).
        
        Args:
            filters: Query filters (date range, buyer info, etc.)
        
        Returns:
            dict: Paginated invoice list
        """
        validated = self._validate(filters, "invoice_query_normal")
        return self.post("invoice_query", validated, encrypt=True)
    
    def query_all_invoices(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query all invoices including credit/debit notes (T106).
        
        Args:
            filters: Query filters
        
        Returns:
            dict: Paginated invoice list
        """
        validated = self._validate(filters, "invoice_query_all")
        return self.post("invoice_query_all", validated, encrypt=True)
    
    def verify_invoices_batch(self, invoice_checks: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Batch verify multiple invoices (T117).
        
        Args:
            invoice_checks: List of {invoiceNo, invoiceType} objects
        
        Returns:
            dict: Verification results
        """
        payload = [
            {"invoiceNo": check["invoiceNo"], "invoiceType": check["invoiceType"]}
            for check in invoice_checks
        ]
        return self.post("invoice_checks", payload, encrypt=True)
    
    # =========================================================================
    # CREDIT/DEBIT NOTE OPERATIONS
    # =========================================================================
    
    def apply_credit_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply for credit note (T110).
        
        Args:
            data: Credit note application data
        
        Returns:
            dict: Application response with referenceNo
        """
        validated = self._validate(data, "credit_application")
        return self.post("credit_application", validated, encrypt=True)
    
    def apply_debit_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply for debit note (T110 with category code 104).
        
        Args:
            data: Debit note application data
        
        Returns:
            dict: Application response
        """
        data["invoiceApplyCategoryCode"] = "104"
        validated = self._validate(data, "credit_application")
        return self.post("credit_application", validated, encrypt=True)
    
    def query_credit_note_status(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query credit/debit note application status (T111).
        
        Args:
            filters: Query filters
        
        Returns:
            dict: Application status list
        """
        validated = self._validate(filters, "credit_note_query")
        return self.post("credit_note_status", validated, encrypt=True)
    
    def get_credit_application_detail(self, application_id: str) -> Dict[str, Any]:
        """
        Get credit note application details (T112).
        
        Args:
            application_id: Application ID
        
        Returns:
            dict: Application details
        """
        validated = self._validate({"id": application_id}, "credit_note_details")
        return self.post("credit_application_detail", validated, encrypt=True)
    
    def approve_credit_note(
        self,
        reference_no: str,
        approve: bool,
        task_id: str,
        remark: str
    ) -> Dict[str, Any]:
        """
        Approve or reject credit note (T113).
        
        Args:
            reference_no: Application reference number
            approve: True to approve, False to reject
            task_id: Task ID from application
            remark: Approval remark
        
        Returns:
            dict: Approval response
        """
        payload = {
            "referenceNo": reference_no,
            "approveStatus": "101" if approve else "103",
            "taskId": task_id,
            "remark": remark
        }
        return self.post("credit_note_approval", payload, encrypt=True)
    
    def cancel_credit_note_application(
        self,
        ori_invoice_id: str,
        invoice_no: str,
        reason_code: str,
        reason: Optional[str] = None,
        cancel_type: str = "104"
    ) -> Dict[str, Any]:
        """
        Cancel credit/debit note application (T114).
        
        Args:
            ori_invoice_id: Original invoice ID
            invoice_no: Invoice number
            reason_code: Cancellation reason code
            reason: Cancellation reason text
            cancel_type: 103=Cancel Debit, 104=Cancel Credit
        
        Returns:
            dict: Cancellation response
        """
        payload = {
            "oriInvoiceId": ori_invoice_id,
            "invoiceNo": invoice_no,
            "reasonCode": reason_code,
            "reason": reason,
            "invoiceApplyCategoryCode": cancel_type
        }
        validated = self._validate(payload, "credit_note_cancel")
        return self.post("credit_note_cancel", validated, encrypt=True)
    
    def query_invalid_credit_note(self, invoice_no: str) -> Dict[str, Any]:
        """
        Query invalid credit note details (T122).
        
        Args:
            invoice_no: Invoice number
        
        Returns:
            dict: Credit note details
        """
        return self.post("query_invalid_credit", {"invoiceNo": invoice_no}, encrypt=True)
    
    def void_credit_debit_application(
        self,
        business_key: str,
        reference_no: str
    ) -> Dict[str, Any]:
        """
        Void credit/debit note application (T120).
        
        Args:
            business_key: Business key
            reference_no: Reference number
        
        Returns:
            dict: Void response
        """
        payload = {"businessKey": business_key, "referenceNo": reference_no}
        return self.post("void_application", payload, encrypt=True)
    
    # =========================================================================
    # TAXPAYER & BRANCH OPERATIONS
    # =========================================================================
    
    def query_taxpayer_by_tin(
        self,
        tin: Optional[str] = None,
        nin_brn: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query taxpayer information (T119).
        
        Args:
            tin: Taxpayer ID
            nin_brn: NIN/BRN
        
        Returns:
            dict: Taxpayer information
        """
        payload = {"tin": tin, "ninBrn": nin_brn}
        validated = self._validate(payload, "query_taxpayer")
        return self.post("query_taxpayer", validated, encrypt=True)
    
    def get_registered_branches(self, tin: Optional[str] = None) -> Dict[str, Any]:
        """
        Get registered branches (T138).
        
        Args:
            tin: Taxpayer ID
        
        Returns:
            dict: Branch list
        """
        payload = {"tin": tin} if tin else {}
        return self.post("get_branches", payload, encrypt=True)
    
    def check_taxpayer_type(self, tin: str) -> Dict[str, Any]:
        """
        Check taxpayer VAT type (T137).
        
        Args:
            tin: Taxpayer ID
        
        Returns:
            dict: Taxpayer type information
        """
        return self.post("check_taxpayer_type", {"tin": tin}, encrypt=True)
    
    # =========================================================================
    # COMMODITY & EXCISE OPERATIONS
    # =========================================================================
    
    def query_commodity_categories(
        self,
        page_no: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Query commodity categories with pagination (T124).
        
        Args:
            page_no: Page number
            page_size: Items per page
        
        Returns:
            dict: Paginated category list
        """
        payload = {"pageNo": page_no, "pageSize": page_size}
        return self.post("query_commodity_category_page", payload, encrypt=False)
    
    def query_commodity_categories_all(self) -> Dict[str, Any]:
        """
        Query all commodity categories (T123).
        
        Returns:
            dict: Category list
        """
        return self.post("query_commodity_category", {}, encrypt=False)
    
    def sync_commodity_categories(self, local_version: str) -> Dict[str, Any]:
        """
        Sync commodity categories incrementally (T134).
        
        Args:
            local_version: Local version number
        
        Returns:
            dict: Updated categories
        """
        return self.post(
            "commodity_incremental",
            {"commodityCategoryVersion": local_version},
            encrypt=True
        )
    
    def query_excise_duty_codes(self) -> Dict[str, Any]:
        """
        Query excise duty codes (T125).
        
        Returns:
            dict: Excise duty list
        """
        return self.post("query_excise_duty", {}, encrypt=False)
    
    # =========================================================================
    # EXCHANGE RATE OPERATIONS
    # =========================================================================
    
    def get_exchange_rate(self, currency: str) -> Dict[str, Any]:
        """
        Get exchange rate for currency (T121).
        
        Args:
            currency: Currency code (e.g., "USD")
        
        Returns:
            dict: Exchange rate information
        """
        return self.post("get_exchange_rate", {"currency": currency}, encrypt=True)
    
    def get_all_exchange_rates(self) -> Dict[str, Any]:
        """
        Get all exchange rates (T126).
        
        Returns:
            dict: All exchange rates
        """
        return self.post("get_exchange_rates", {}, encrypt=False)
    
    # =========================================================================
    # GOODS & STOCK OPERATIONS
    # =========================================================================
    
    def upload_goods(self, goods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload goods to EFRIS (T130).
        
        Args:
            goods: List of goods data
        
        Returns:
            dict: Upload results
        """
        return self.post("goods_upload", goods, encrypt=True)
    
    def inquire_goods(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inquire goods (T127).
        
        Args:
            filters: Query filters
        
        Returns:
            dict: Goods list
        """
        return self.post("goods_inquiry", filters, encrypt=True)
    
    def query_goods_by_code(
        self,
        goods_code: str,
        tin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query goods by code (T144).
        
        Args:
            goods_code: Goods code
            tin: Taxpayer ID
        
        Returns:
            dict: Goods information
        """
        payload = {"goodsCode": goods_code}
        if tin:
            payload["tin"] = tin
        return self.post("query_goods_by_code", payload, encrypt=True)
    
    def query_stock_quantity(self, goods_id: str) -> Dict[str, Any]:
        """
        Query stock quantity (T128).
        
        Args:
            goods_id: Goods ID
        
        Returns:
            dict: Stock information
        """
        return self.post("query_stock", {"id": goods_id}, encrypt=True)
    
    def maintain_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maintain stock levels (T131).
        
        Args:
            data: Stock maintenance data
        
        Returns:
            dict: Maintenance results
        """
        validated = self._validate(data, "stock_maintain")
        return self.post("stock_maintain", validated, encrypt=True)
    
    def transfer_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transfer stock between branches (T139).
        
        Args:
            data: Transfer data
        
        Returns:
            dict: Transfer results
        """
        return self.post("stock_transfer", data, encrypt=True)
    
    # =========================================================================
    # REPORTING & LOGGING
    # =========================================================================
    
    def upload_z_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload Z-report (T116).
        
        Args:
            report_data: Z-report data
        
        Returns:
            dict: Upload response
        """
        return self.post("z_report_upload", report_data, encrypt=True)
    
    def upload_exception_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload exception logs (T132).
        
        Args:
            logs: List of exception log entries
        
        Returns:
            dict: Upload response
        """
        payload = [
            {
                "interruptionTypeCode": log["interruptionTypeCode"],
                "description": log["description"],
                "errorDetail": log.get("errorDetail"),
                "interruptionTime": log["interruptionTime"]
            }
            for log in logs
        ]
        return self.post("exception_log_upload", payload, encrypt=True)
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_server_time(self) -> str:
        """
        Get server time (T101).
        
        Returns:
            str: Server timestamp
        """
        resp = self.test_interface()
        if "data" in resp and "content" in resp["data"]:
            return resp["data"]["content"].get("currentTime")
        return resp.get("currentTime", "")
    
    def is_time_synced(self, tolerance_minutes: int = 10) -> bool:
        """
        Check if client time is synchronized with server.
        
        Args:
            tolerance_minutes: Maximum allowed difference
        
        Returns:
            bool: True if synchronized
        """
        from .utils import get_uganda_timestamp, validate_time_sync
        server_time_str = self.get_server_time()
        if not server_time_str:
            return False
        client_time_str = get_uganda_timestamp()
        return validate_time_sync(client_time_str, server_time_str, tolerance_minutes)
    
    def refresh_aes_key_if_needed(self) -> bool:
        """
        Refresh AES key if expired or not set.
        
        Returns:
            bool: True if key was refreshed
        """
        import time
        if self.key_client._aes_key_fetched_at:
            elapsed = time.time() - self.key_client._aes_key_fetched_at
            if elapsed > (23 * 60 * 60):  # 23 hours
                self.key_client.fetch_aes_key(force=True)
                return True
        elif not self.key_client._aes_key:
            self.key_client.fetch_aes_key()
            return True
        return False