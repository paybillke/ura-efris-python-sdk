"""
EFRIS Base Client
Provides core HTTP communication and request/response handling.
All API clients inherit from this base class.
"""
import requests
import json
from typing import Dict, Any, Optional
from .utils import (
    build_encrypted_request,
    build_unencrypted_request,
    unwrap_response,
    get_uganda_timestamp
)
from .exceptions import ApiException, EncryptionException
from .key_client import KeyClient


class BaseClient:
    """
    Base client for EFRIS API communication.
    
    Handles:
        - HTTP request/response lifecycle
        - Request encryption/decryption
        - Interface code mapping
        - Endpoint URL resolution
    
    Note: This is a base class. Use Client class for business logic methods.
    """
    
    # Interface code mapping (API endpoint identifiers)
    INTERFACES = {
        "test_interface": "T101",
        "client_init": "T102",
        "sign_in": "T103",
        "get_symmetric_key": "T104",
        "forget_password": "T105",
        "system_dictionary": "T115",
        "query_taxpayer": "T119",
        "get_branches": "T138",
        "check_taxpayer_type": "T137",
        "query_commodity_category": "T123",
        "query_commodity_category_page": "T124",
        "query_excise_duty": "T125",
        "get_exchange_rates": "T126",
        "get_exchange_rate": "T121",
        "goods_upload": "T130",
        "goods_inquiry": "T127",
        "query_stock": "T128",
        "stock_maintain": "T131",
        "stock_transfer": "T139",
        "query_goods_by_code": "T144",
        "invoice_query_all": "T106",
        "invoice_query": "T107",
        "invoice_details": "T108",
        "billing_upload": "T109",
        "batch_invoice_upload": "T129",
        "credit_application": "T110",
        "credit_note_status": "T111",
        "credit_note_cancel": "T114",
        "query_credit_application": "T118",
        "credit_application_detail": "T112",
        "credit_note_approval": "T113",
        "void_application": "T120",
        "query_invalid_credit": "T122",
        "invoice_checks": "T117",
        "exception_log_upload": "T132",
        "commodity_incremental": "T134",
        "z_report_upload": "T116",
    }
    
    def __init__(self, config: Dict[str, Any], key_client: "KeyClient"):
        """
        Initialize base client with configuration and key manager.
        
        Args:
            config: Configuration dictionary (from config.py)
            key_client: KeyClient instance for cryptographic operations
        """
        self.config = config
        self.key_client = key_client
        self.timeout = config.get("http", {}).get("timeout", 30)
    
    def _get_endpoint_url(self) -> str:
        """
        Get the API endpoint URL based on environment.
        
        Returns:
            str: API endpoint URL
        """
        env = self.config.get("env", "sbx")
        if env == "sbx":
            return "https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation"
        return "https://efrisws.ura.go.ug/ws/taapp/getInformation"
    
    def _send(
        self,
        interface_key: str,
        payload: Dict[str, Any],
        encrypt: bool = True
    ) -> Dict[str, Any]:
        """
        Send HTTP request to EFRIS API.
        
        Process:
            1. Validate interface code
            2. Fetch AES key if encryption is enabled
            3. Build request envelope (encrypted or unencrypted)
            4. Send HTTP POST request
            5. Unwrap and decrypt response
        
        Args:
            interface_key: Interface name from INTERFACES dict
            payload: Request payload dictionary
            encrypt: Whether to encrypt the request
        
        Returns:
            dict: API response dictionary
        
        Raises:
            ApiException: If interface not configured or HTTP error
            EncryptionException: If encryption/decryption fails
        """
        # Validate interface code
        if interface_key not in self.INTERFACES:
            raise ApiException(
                f"Interface [{interface_key}] not configured",
                status_code=400
            )
        
        interface_code = self.INTERFACES[interface_key]
        aes_key = None
        
        # Fetch AES key for encryption
        if encrypt:
            aes_key = self.key_client.fetch_aes_key()
        
        # Build request envelope
        if encrypt and aes_key:
            private_key = self.key_client._load_private_key()
            request_envelope = build_encrypted_request(
                content=payload,
                aes_key=aes_key,
                interface_code=interface_code,
                tin=self.config["tin"],
                device_no=self.config["device_no"],
                brn=self.config.get("brn", ""),
                private_key=private_key
            )
        else:
            request_envelope = build_unencrypted_request(
                content=payload,
                interface_code=interface_code,
                tin=self.config["tin"],
                device_no=self.config["device_no"],
                brn=self.config.get("brn", "")
            )
        
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
            raise ApiException(
                f"HTTP {response.status_code}: {response.text}",
                status_code=response.status_code
            )
        
        # Parse JSON response
        try:
            resp_json = response.json()
        except json.JSONDecodeError as e:
            raise ApiException(f"Invalid JSON response: {e}", status_code=500)
        
        # Decrypt response if encrypted
        if encrypt and aes_key:
            return unwrap_response(resp_json, aes_key)
        
        return resp_json
    
    def get(
        self,
        interface_key: str,
        params: Optional[Dict] = None,
        encrypt: bool = True
    ) -> Dict:
        """
        Send GET-style request (uses POST with params).
        
        Args:
            interface_key: Interface name
            params: Request parameters
            encrypt: Whether to encrypt
        
        Returns:
            dict: API response
        """
        return self._send(interface_key, params or {}, encrypt=encrypt)
    
    def post(
        self,
        interface_key: str,
        data: Optional[Dict] = None,
        encrypt: bool = True
    ) -> Dict:
        """
        Send POST-style request.
        
        Args:
            interface_key: Interface name
            data: Request data
            encrypt: Whether to encrypt
        
        Returns:
            dict: API response
        """
        return self._send(interface_key, data or {}, encrypt=encrypt)