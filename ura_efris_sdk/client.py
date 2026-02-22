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
import logging

logger = logging.getLogger(__name__)


class Client(BaseClient):
    """
    Main EFRIS API client with business logic methods.
    
    Provides validated methods for:
        - Authentication (sign_in, get_symmetric_key)
        - Invoice operations (upload, query, verify)
        - Credit/Debit note operations
        - Goods and stock management
        - System queries (dictionary, exchange rates, etc.)
        - EDC/Fuel operations
        - Agent/USSD operations
        - Export/Customs operations
    
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
   
    def client_init(self) -> Dict[str, Any]:
        """T102: Client Initialization - Returns server public key."""
        return self._send("client_init", {}, encrypt=False, decrypt=False)
    
    def sign_in(self) -> Dict[str, Any]:
        """T103: Sign In - Login and retrieve taxpayer/device information."""
        response = self._send("sign_in", {}, encrypt=False, decrypt=True)
        content = response.get("data", {}).get("content", {})
        taxpayer = content.get("taxpayer", {})
        if taxpayer and "id" in taxpayer:
            self.key_client.taxpayer_id = str(taxpayer["id"])
            logger.debug(f"Updated taxpayerID from sign_in: {self.key_client.taxpayer_id}")
        return response
    
    def get_symmetric_key(self, force: bool = False) -> Dict[str, Any]:
        """T104: Get Symmetric Key - Fetch AES key for encryption."""
        self.key_client.fetch_aes_key(force=force)
        return self.key_client._aes_key_content_json or {}
    
    def forget_password(self, user_name: str, new_password: str) -> Dict[str, Any]:
        """T105: Forget Password - Reset user password."""
        payload = {"userName": user_name, "changedPassword": new_password}
        return self._send("forget_password", payload, encrypt=True, decrypt=False)
    
    def update_system_dictionary(self, data: Optional[Dict] = None) -> Dict[str, Any]:
        """T115: System Dictionary Update - Get tax rates, currencies, etc."""
        return self._send("system_dictionary", data or {}, encrypt=False, decrypt=True)
    
    # =========================================================================
    # INVOICE OPERATIONS
    # =========================================================================
    
    def fiscalise_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T109: Billing Upload - Upload invoice/receipt/debit note."""
        validated = self._validate(data, "billing_upload")
        return self._send("billing_upload", validated, encrypt=True, decrypt=True)
    
    def fiscalise_batch_invoices(self, invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """T129: Batch Invoice Upload - Upload multiple invoices."""
        payload = [
            {"invoiceContent": inv.get("invoiceContent", ""), "invoiceSignature": inv.get("invoiceSignature", "")}
            for inv in invoices
        ]
        return self._send("batch_invoice_upload", payload, encrypt=True, decrypt=True)
    
    def verify_invoice(self, invoice_no: str) -> Dict[str, Any]:
        """T108: Invoice Details - Get full invoice details."""
        validated = self._validate({"invoiceNo": invoice_no}, "invoice_details")
        return self._send("invoice_details", validated, encrypt=True, decrypt=True)
    
    def query_invoices(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T107: Query Normal Invoice/Receipt - For credit/debit note eligibility."""
        validated = self._validate(filters, "invoice_query_normal")
        return self._send("invoice_query_normal", validated, encrypt=True, decrypt=True)
    
    def query_all_invoices(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T106: Invoice/Receipt Query - All invoice types with pagination."""
        validated = self._validate(filters, "invoice_query_all")
        return self._send("invoice_query_all", validated, encrypt=True, decrypt=True)
    
    def verify_invoices_batch(self, invoice_checks: List[Dict[str, str]]) -> Dict[str, Any]:
        """T117: Invoice Checks - Batch verify multiple invoices."""
        payload = [{"invoiceNo": c["invoiceNo"], "invoiceType": c["invoiceType"]} for c in invoice_checks]
        return self._send("invoice_checks", payload, encrypt=True, decrypt=True)
    
    def invoice_remain_details(self, invoice_no: str) -> Dict[str, Any]:
        """T186: Invoice Remain Details - Get invoice with remaining quantities."""
        validated = self._validate({"invoiceNo": invoice_no}, "invoice_remain_details")
        return self._send("invoice_remain_details", validated, encrypt=True, decrypt=True)
    
    # =========================================================================
    # CREDIT/DEBIT NOTE OPERATIONS
    # =========================================================================
    
    def apply_credit_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T110: Credit Application - Apply for credit note."""
        data["invoiceApplyCategoryCode"] = data.get("invoiceApplyCategoryCode", "101")
        validated = self._validate(data, "credit_application")
        return self._send("credit_application", validated, encrypt=True, decrypt=True)
    
    def apply_debit_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T110: Debit Note Application - Apply for debit note."""
        data["invoiceApplyCategoryCode"] = "104"
        validated = self._validate(data, "credit_application")
        return self._send("credit_application", validated, encrypt=True, decrypt=True)
    
    def query_credit_note_status(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T111: Credit/Debit Note Application List Query."""
        validated = self._validate(filters, "credit_note_query")
        return self._send("credit_note_query", validated, encrypt=True, decrypt=True)
    
    def get_credit_application_detail(self, application_id: str) -> Dict[str, Any]:
        """T112: Credit Note Application Details."""
        validated = self._validate({"id": application_id}, "credit_note_details")
        return self._send("credit_application_detail", validated, encrypt=True, decrypt=True)
    
    def approve_credit_note(self, reference_no: str, approve: bool, task_id: str, remark: str) -> Dict[str, Any]:
        """T113: Credit Note Approval - Approve or reject application."""
        payload = {"referenceNo": reference_no, "approveStatus": "101" if approve else "103", "taskId": task_id, "remark": remark}
        return self._send("credit_note_approval", payload, encrypt=True, decrypt=False)
    
    def cancel_credit_note_application(self, ori_invoice_id: str, invoice_no: str, reason_code: str, 
                                       reason: Optional[str] = None, cancel_type: str = "104") -> Dict[str, Any]:
        """T114: Cancel Credit/Debit Note Application."""
        payload = {"oriInvoiceId": ori_invoice_id, "invoiceNo": invoice_no, "reasonCode": reason_code, 
                   "reason": reason, "invoiceApplyCategoryCode": cancel_type}
        validated = self._validate(payload, "credit_note_cancel")
        return self._send("credit_note_cancel", validated, encrypt=True, decrypt=False)
    
    def query_invalid_credit_note(self, invoice_no: str) -> Dict[str, Any]:
        """T122: Query Cancel Credit Note Details."""
        return self._send("query_invalid_credit", {"invoiceNo": invoice_no}, encrypt=True, decrypt=True)
    
    def void_credit_debit_application(self, business_key: str, reference_no: str) -> Dict[str, Any]:
        """T120: Void Credit/Debit Note Application."""
        payload = {"businessKey": business_key, "referenceNo": reference_no}
        return self._send("void_application", payload, encrypt=True, decrypt=False)
    
    # =========================================================================
    # TAXPAYER & BRANCH OPERATIONS
    # =========================================================================
    
    def query_taxpayer_by_tin(self, tin: Optional[str] = None, nin_brn: Optional[str] = None) -> Dict[str, Any]:
        """T119: Query Taxpayer Information By TIN."""
        payload = {"tin": tin, "ninBrn": nin_brn}
        validated = self._validate(payload, "query_taxpayer")
        return self._send("query_taxpayer", validated, encrypt=True, decrypt=True)
    
    def get_registered_branches(self, tin: Optional[str] = None) -> Dict[str, Any]:
        """T138: Get All Branches."""
        payload = {"tin": tin} if tin else {}
        return self._send("get_branches", payload, encrypt=True, decrypt=True)
    
    def check_taxpayer_type(self, tin: str, commodity_category_code: Optional[str] = None) -> Dict[str, Any]:
        """T137: Check Exempt/Deemed Taxpayer."""
        payload = {"tin": tin}
        if commodity_category_code:
            payload["commodityCategoryCode"] = commodity_category_code
        return self._send("check_taxpayer_type", payload, encrypt=True, decrypt=True)
    
    def query_principal_agent(self, tin: str, branch_id: str) -> Dict[str, Any]:
        """T180: Query Principal Agent TIN Information."""
        payload = {"tin": tin, "branchId": branch_id}
        return self._send("query_principal_agent", payload, encrypt=True, decrypt=True)
    
    # =========================================================================
    # COMMODITY & EXCISE OPERATIONS
    # =========================================================================
    
    def query_commodity_categories(self, page_no: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """T124: Query Commodity Category Pagination."""
        payload = {"pageNo": page_no, "pageSize": page_size}
        return self._send("query_commodity_category_page", payload, encrypt=False, decrypt=False)
    
    def query_commodity_categories_all(self) -> Dict[str, Any]:
        """T123: Query All Commodity Categories."""
        return self._send("query_commodity_category", {}, encrypt=False, decrypt=False)
    
    def sync_commodity_categories(self, local_version: str) -> Dict[str, Any]:
        """T134: Commodity Category Incremental Update."""
        return self._send("commodity_incremental", {"commodityCategoryVersion": local_version}, encrypt=True, decrypt=True)
    
    def query_commodity_by_date(self, category_code: str, item_type: str, issue_date: str) -> Dict[str, Any]:
        """T146: Query Commodity/Excise Duty by Issue Date."""
        payload = {"categoryCode": category_code, "type": item_type, "issueDate": issue_date}
        return self._send("query_commodity_by_date", payload, encrypt=True, decrypt=True)
    
    def query_excise_duty_codes(self) -> Dict[str, Any]:
        """T125: Query Excise Duty Codes."""
        return self._send("query_excise_duty", {}, encrypt=False, decrypt=False)
    
    def query_hs_codes(self) -> Dict[str, Any]:
        """T185: Query HS Code List."""
        return self._send("query_hs_codes", {}, encrypt=False, decrypt=False)
    
    # =========================================================================
    # EXCHANGE RATE OPERATIONS
    # =========================================================================
    
    def get_exchange_rate(self, currency: str, issue_date: Optional[str] = None) -> Dict[str, Any]:
        """T121: Acquire Exchange Rate for Single Currency."""
        payload = {"currency": currency}
        if issue_date:
            payload["issueDate"] = issue_date
        return self._send("get_exchange_rate", payload, encrypt=True, decrypt=True)
    
    def get_all_exchange_rates(self, issue_date: Optional[str] = None) -> Dict[str, Any]:
        """T126: Get All Exchange Rates."""
        payload = {}
        if issue_date:
            payload["issueDate"] = issue_date
        return self._send("get_exchange_rates", payload, encrypt=True, decrypt=True)
    
    # =========================================================================
    # GOODS & STOCK OPERATIONS
    # =========================================================================
    
    def upload_goods(self, goods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """T130: Goods Upload - Add or modify goods."""
        return self._send("goods_upload", goods, encrypt=True, decrypt=True)
    
    def inquire_goods(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T127: Goods/Services Inquiry with pagination."""
        return self._send("goods_inquiry", filters, encrypt=True, decrypt=True)
    
    def query_goods_by_code(self, goods_code: str, tin: Optional[str] = None) -> Dict[str, Any]:
        """T144: Query Goods by Code."""
        payload = {"goodsCode": goods_code}
        if tin:
            payload["tin"] = tin
        return self._send("query_goods_by_code", payload, encrypt=True, decrypt=True)
    
    def query_stock_quantity(self, goods_id: str, branch_id: Optional[str] = None) -> Dict[str, Any]:
        """T128: Query Stock Quantity by Goods ID."""
        payload = {"id": goods_id}
        if branch_id:
            payload["branchId"] = branch_id
        return self._send("query_stock", payload, encrypt=True, decrypt=True)
    
    def maintain_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T131: Goods Stock Maintain - Stock in/out operations."""
        validated = self._validate(data, "stock_maintain")
        return self._send("stock_maintain", validated, encrypt=True, decrypt=True)
    
    def transfer_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T139: Goods Stock Transfer Between Branches."""
        return self._send("stock_transfer", data, encrypt=True, decrypt=True)
    
    def query_stock_records(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T145: Goods Stock Records Query."""
        return self._send("stock_records_query", filters, encrypt=True, decrypt=True)
    
    def query_stock_records_alt(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T147: Goods Stock Records Query (Current Branch Only)."""
        return self._send("stock_records_query_alt", filters, encrypt=True, decrypt=True)
    
    def query_stock_record_detail(self, record_id: str) -> Dict[str, Any]:
        """T148: Goods Stock Record Detail Query."""
        return self._send("stock_records_detail", {"id": record_id}, encrypt=True, decrypt=True)
    
    def query_stock_adjust_records(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T149: Goods Stock Adjust Records Query."""
        return self._send("stock_adjust_records", filters, encrypt=True, decrypt=True)
    
    def query_stock_adjust_detail(self, adjust_id: str) -> Dict[str, Any]:
        """T160: Goods Stock Adjust Detail Query."""
        return self._send("stock_adjust_detail", {"id": adjust_id}, encrypt=True, decrypt=True)
    
    def query_stock_transfer_records(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T183: Goods Stock Transfer Records Query."""
        return self._send("stock_transfer_records", filters, encrypt=True, decrypt=True)
    
    def query_stock_transfer_detail(self, transfer_id: str) -> Dict[str, Any]:
        """T184: Goods Stock Transfer Detail Query."""
        return self._send("stock_transfer_detail", {"id": transfer_id}, encrypt=True, decrypt=True)
    
    def query_negative_stock_config(self) -> Dict[str, Any]:
        """T177: Negative Stock Configuration Inquiry."""
        return self._send("negative_stock_config", {}, encrypt=False, decrypt=False)
    
    # =========================================================================
    # EDC / FUEL SPECIFIC OPERATIONS
    # =========================================================================
    
    def query_fuel_type(self) -> Dict[str, Any]:
        """T162: Query Fuel Type."""
        return self._send("query_fuel_type", {}, encrypt=False, decrypt=True)
    
    def upload_shift_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T163: Upload Shift Information."""
        return self._send("upload_shift_info", data, encrypt=True, decrypt=False)
    
    def upload_edc_disconnect(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """T164: Upload EDC Disconnection Data."""
        return self._send("upload_edc_disconnect", logs, encrypt=True, decrypt=False)
    
    def update_buyer_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T166: Update Buyer Details on EDC Invoice."""
        return self._send("update_buyer_details", data, encrypt=True, decrypt=False)
    
    def edc_invoice_query(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """T167: EDC Invoice/Receipt Inquiry."""
        return self._send("edc_invoice_query", filters, encrypt=True, decrypt=True)
    
    def query_fuel_pump_version(self) -> Dict[str, Any]:
        """T168: Query Fuel Pump Version."""
        return self._send("query_fuel_pump_version", {}, encrypt=False, decrypt=True)
    
    def query_pump_nozzle_tank(self, pump_id: str) -> Dict[str, Any]:
        """T169: Query Pump/Nozzle/Tank by Pump Number."""
        return self._send("query_pump_nozzle_tank", {"id": pump_id}, encrypt=True, decrypt=True)
    
    def query_edc_location(self, device_number: str, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> Dict[str, Any]:
        """T170: Query EFD Location History."""
        payload = {"deviceNumber": device_number}
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        return self._send("query_edc_location", payload, encrypt=True, decrypt=True)
    
    def query_edc_uom_rate(self) -> Dict[str, Any]:
        """T171: Query EDC UoM Exchange Rate."""
        return self._send("query_edc_uom_rate", {}, encrypt=False, decrypt=True)
    
    def upload_nozzle_status(self, nozzle_id: str, nozzle_no: str, status: str) -> Dict[str, Any]:
        """T172: Fuel Nozzle Status Upload."""
        payload = {"nozzleId": nozzle_id, "nozzleNo": nozzle_no, "status": status}
        return self._send("upload_nozzle_status", payload, encrypt=True, decrypt=False)
    
    def query_edc_device_version(self) -> Dict[str, Any]:
        """T173: Query EDC Device Version."""
        return self._send("query_edc_device_version", {}, encrypt=False, decrypt=True)
    
    def upload_device_status(self, device_no: str, status: str) -> Dict[str, Any]:
        """T176: Upload Device Issuing Status."""
        payload = {"deviceNo": device_no, "deviceIssuingStatus": status}
        return self._send("upload_device_status", payload, encrypt=False, decrypt=False)
    
    # =========================================================================
    # AGENT / USSD / FREQUENT CONTACTS
    # =========================================================================
    
    def ussd_account_create(self, tin: str, mobile_number: str) -> Dict[str, Any]:
        """T175: Account Creation for USSD Taxpayer."""
        payload = {"tin": tin, "mobileNumber": mobile_number}
        return self._send("ussd_account_create", payload, encrypt=True, decrypt=False)
    
    def efd_transfer(self, destination_branch_id: str, remarks: Optional[str] = None) -> Dict[str, Any]:
        """T178: EFD Transfer to Another Branch."""
        payload = {"destinationBranchId": destination_branch_id}
        if remarks:
            payload["remarks"] = remarks
        return self._send("efd_transfer", payload, encrypt=True, decrypt=False)
    
    def query_agent_relation(self, tin: str) -> Dict[str, Any]:
        """T179: Query Agent Relation Information."""
        return self._send("query_agent_relation", {"tin": tin}, encrypt=True, decrypt=True)
    
    def upload_frequent_contacts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """T181: Upload Frequent Contacts."""
        return self._send("upload_frequent_contacts", data, encrypt=True, decrypt=False)
    
    def get_frequent_contacts(self, buyer_tin: Optional[str] = None, 
                           buyer_legal_name: Optional[str] = None) -> Dict[str, Any]:
        """T182: Get Frequent Contacts."""
        payload = {}
        if buyer_tin:
            payload["buyerTin"] = buyer_tin
        if buyer_legal_name:
            payload["buyerLegalName"] = buyer_legal_name
        return self._send("get_frequent_contacts", payload, encrypt=True, decrypt=True)
    
    # =========================================================================
    # EXPORT / CUSTOMS OPERATIONS
    # =========================================================================
    
    def query_fdn_status(self, invoice_no: str) -> Dict[str, Any]:
        """T187: Query Export FDN Status."""
        return self._send("query_fdn_status", {"invoiceNo": invoice_no}, encrypt=True, decrypt=True)
    
    # =========================================================================
    # REPORTING & LOGGING
    # =========================================================================
    
    def upload_z_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """T116: Z-Report Daily Upload."""
        return self._send("z_report_upload", report_data, encrypt=True, decrypt=True)
    
    def upload_exception_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """T132: Upload Exception Logs."""
        payload = [{"interruptionTypeCode": l["interruptionTypeCode"], "description": l["description"], 
                   "errorDetail": l.get("errorDetail"), "interruptionTime": l["interruptionTime"]} for l in logs]
        return self._send("exception_log_upload", payload, encrypt=True, decrypt=False)
    
    def tcs_upgrade_download(self, tcs_version: str, os_type: str) -> Dict[str, Any]:
        """T133: TCS Upgrade System File Download."""
        payload = {"tcsVersion": tcs_version, "osType": os_type}
        return self._send("tcs_upgrade_download", payload, encrypt=True, decrypt=True)
    
    def get_tcs_latest_version(self) -> Dict[str, Any]:
        """T135: Get TCS Latest Version."""
        return self._send("get_tcs_latest_version", {}, encrypt=False, decrypt=True)
    
    def certificate_upload(self, file_name: str, verify_string: str, file_content: str) -> Dict[str, Any]:
        """T136: Certificate Public Key Upload."""
        payload = {"fileName": file_name, "verifyString": verify_string, "fileContent": file_content}
        return self._send("certificate_upload", payload, encrypt=False, decrypt=False)
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_server_time(self) -> str:
        """Get server time (T101)."""
        return self._send("get_server_time", {}, encrypt=False, decrypt=False)
    
    def is_time_synced(self, tolerance_minutes: int = 10, max_retries: int = 3) -> bool:
        """Check if client time is synchronized with server."""
        from .utils import get_uganda_timestamp, validate_time_sync
        import time
        
        for attempt in range(max_retries):
            try:
                server_time_str = self.get_server_time()
                if not server_time_str:
                    logger.warning(f"Attempt {attempt+1}: Could not retrieve server time")
                    time.sleep(1)
                    continue
                client_time_str = get_uganda_timestamp()
                if validate_time_sync(client_time_str, server_time_str, tolerance_minutes):
                    if attempt > 0:
                        logger.info(f"Time sync successful after {attempt+1} attempt(s)")
                    return True
                logger.warning(f"Attempt {attempt+1}: Time sync failed")
                if attempt < max_retries - 1:
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}: Time sync check error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        logger.error(f"Time sync failed after {max_retries} attempts")
        return False
    
    def refresh_aes_key_if_needed(self) -> bool:
        """Refresh AES key if expired or not set."""
        import time
        if self.key_client._aes_key_fetched_at:
            elapsed = time.time() - self.key_client._aes_key_fetched_at
            if elapsed > (23 * 60 * 60):
                self.key_client.fetch_aes_key(force=True)
                return True
        elif not self.key_client._aes_key:
            self.key_client.fetch_aes_key()
            return True
        return False