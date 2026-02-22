"""
EFRIS Base Client
Provides core HTTP communication and request/response handling.
All API clients inherit from this base class.
"""
import requests
import json
import logging
from typing import Dict, Any, Optional
from .utils import (
    build_encrypted_request,
    build_unencrypted_request,
    unwrap_response
)
from .exceptions import EncryptionException, APIException
from .key_client import KeyClient


class BaseClient:
    """
    Base client for EFRIS API communication.
    
    Handles:
        - HTTP request/response lifecycle
        - Request encryption/decryption
        - Interface code mapping
        - Endpoint URL resolution
    """
    
    # =====================================================================
    # COMPLETE INTERFACE CODE MAPPING (All endpoints from EFRIS v23.0)
    # =====================================================================
    INTERFACES = {
        # === SYSTEM / AUTHENTICATION ===
        "get_server_time": "T101",
        "client_init": "T102",
        "sign_in": "T103",
        "get_symmetric_key": "T104",
        "forget_password": "T105",
        
        # === INVOICE MANAGEMENT ===
        "invoice_query_all": "T106",
        "invoice_query_normal": "T107",
        "invoice_details": "T108",
        "billing_upload": "T109",
        "batch_invoice_upload": "T129",
        
        # === CREDIT / DEBIT NOTES ===
        "credit_application": "T110",
        "credit_note_query": "T111",
        "credit_note_details": "T112",
        "credit_note_approval": "T113",
        "credit_note_cancel": "T114",
        "query_credit_application": "T118",
        "void_application": "T120",
        "query_invalid_credit": "T122",
        "invoice_checks": "T117",
        
        # === TAXPAYER / BRANCH ===
        "query_taxpayer": "T119",
        "get_branches": "T138",
        "check_taxpayer_type": "T137",
        "query_principal_agent": "T180",
        
        # === COMMODITY / EXCISE / DICTIONARY ===
        "system_dictionary": "T115",
        "query_commodity_category": "T123",
        "query_commodity_category_page": "T124",
        "query_excise_duty": "T125",
        "commodity_incremental": "T134",
        "query_commodity_by_date": "T146",
        "query_hs_codes": "T185",
        
        # === EXCHANGE RATES ===
        "get_exchange_rates": "T126",
        "get_exchange_rate": "T121",
        
        # === GOODS / SERVICES ===
        "goods_upload": "T130",
        "goods_inquiry": "T127",
        "query_stock": "T128",
        "query_goods_by_code": "T144",
        
        # === STOCK MANAGEMENT ===
        "stock_maintain": "T131",
        "stock_transfer": "T139",
        "stock_records_query": "T145",
        "stock_records_query_alt": "T147",
        "stock_records_detail": "T148",
        "stock_adjust_records": "T149",
        "stock_adjust_detail": "T160",
        "stock_transfer_records": "T183",
        "stock_transfer_detail": "T184",
        "negative_stock_config": "T177",
        
        # === EDC / FUEL SPECIFIC ===
        "query_fuel_type": "T162",
        "upload_shift_info": "T163",
        "upload_edc_disconnect": "T164",
        "update_buyer_details": "T166",
        "edc_invoice_query": "T167",
        "query_fuel_pump_version": "T168",
        "query_pump_nozzle_tank": "T169",
        "query_edc_location": "T170",
        "query_edc_uom_rate": "T171",
        "upload_nozzle_status": "T172",
        "query_edc_device_version": "T173",
        
        # === AGENT / USSD ===
        "ussd_account_create": "T175",
        "upload_device_status": "T176",
        "efd_transfer": "T178",
        "query_agent_relation": "T179",
        "upload_frequent_contacts": "T181",
        "get_frequent_contacts": "T182",
        
        # === EXPORT / CUSTOMS ===
        "invoice_remain_details": "T186",
        "query_fdn_status": "T187",
        
        # === SYSTEM UTILITIES ===
        "z_report_upload": "T116",
        "exception_log_upload": "T132",
        "tcs_upgrade_download": "T133",
        "get_tcs_latest_version": "T135",
        "certificate_upload": "T136",
    }
    
    def __init__(self, config: Dict[str, Any], key_client: "KeyClient"):
        """
        Initialize base client with configuration and key manager.
        
        Args:
            config: Configuration dictionary
            key_client: KeyClient instance for cryptographic operations
        """
        self.config = config
        self.key_client = key_client
        self.timeout = config.get("http", {}).get("timeout", 30)
        self.logger = logging.getLogger(__name__)
    
    def _get_endpoint_url(self) -> str:
        """Get the API endpoint URL based on environment."""
        env = self.config.get("env", "sbx")
        if env == "sbx":
            return "https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation"
        return "https://efrisws.ura.go.ug/ws/taapp/getInformation"
    
    def _send(
        self,
        interface_key: str,
        payload: Dict[str, Any],
        encrypt: bool = True,
        decrypt: bool = False
    ) -> Dict[str, Any]:
        """
        Send HTTP request to EFRIS API.
        
        Args:
            interface_key: Interface name from INTERFACES dict
            payload: Request payload dictionary
            encrypt: Whether to encrypt the request
            decrypt: Whether to decrypt the response
        
        Returns:
            dict: API response dictionary
        
        Raises:
            APIException: If interface not configured or HTTP error
            EncryptionException: If encryption/decryption fails
        """
        # Validate interface code
        if interface_key not in self.INTERFACES:
            raise APIException(
                f"Interface [{interface_key}] not configured",
                status_code=400
            )
        
        interface_code = self.INTERFACES[interface_key]
        aes_key = None
        
        # Fetch AES key for encryption/decryption
        if encrypt or decrypt:
            aes_key = self.key_client.fetch_aes_key()
            if not aes_key:
                raise EncryptionException("AES symmetric key not available")
        
        # Load private key for signing (if encrypting)
        private_key = self.key_client._load_private_key()
        
        # Build request envelope
        if encrypt and aes_key and private_key:
            request_envelope = build_encrypted_request(
                content=payload,
                aes_key=aes_key,
                interface_code=interface_code,
                tin=self.config["tin"],
                device_no=self.config["device_no"],
                brn=self.config.get("brn", ""),
                private_key=private_key,
                taxpayer_id=self.key_client.taxpayer_id
            )
        else:
            request_envelope = build_unencrypted_request(
                content=payload,
                interface_code=interface_code,
                tin=self.config["tin"],
                device_no=self.config["device_no"],
                brn=self.config.get("brn", ""),
                private_key=private_key,
                taxpayer_id=self.key_client.taxpayer_id
            )
        
        # Debug logging (enable in development)
        self.logger.debug(f"Sending request to interface {interface_code}")
        self.logger.debug(f"Encrypt: {encrypt}, Decrypt: {decrypt}")
        
        # Send HTTP request
        url = self._get_endpoint_url()
        response = requests.post(
            url,
            json=request_envelope,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        
        # Handle HTTP errors
        if response.status_code != 200:
            raise APIException(
                f"HTTP {response.status_code}: {response.text}",
                status_code=response.status_code
            )
        
        # Parse JSON response
        try:
            resp_json = response.json()
        except json.JSONDecodeError as e:
            raise APIException(f"Invalid JSON response: {e}", status_code=500)
        
        # Debug: Log response before unwrapping
        self.logger.debug(f"Response returnCode: {resp_json.get('returnStateInfo', {}).get('returnCode')}")
        
        # Unwrap and decrypt response
        return unwrap_response(resp_json, aes_key if decrypt else None)
    
    def get(
        self,
        interface_key: str,
        params: Optional[Dict] = None,
        encrypt: bool = True,
        decrypt: bool = False
    ) -> Dict:
        """Send GET-style request (uses POST with params)."""
        return self._send(interface_key, params or {}, encrypt=encrypt, decrypt=decrypt)
    
    def post(
        self,
        interface_key: str,
        data: Optional[Dict] = None,
        encrypt: bool = True,
        decrypt: bool = False
    ) -> Dict:
        """Send POST-style request."""
        return self._send(interface_key, data or {}, encrypt=encrypt, decrypt=decrypt)