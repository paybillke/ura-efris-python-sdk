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
    Base HTTP client for EFRIS API.
    Handles encryption, signing, request/response wrapping per URA v1.5.
    """
    
    # Interface code mapping (URA v1.5, page 7-10)
    INTERFACES = {
        # System Setup & Encryption
        "test_interface": "T101",           # Test connection (time sync)
        "get_symmetric_key": "T104",        # Get AES key (mandatory)
        "system_dictionary": "T115",        # System dictionary update
        
        # Registration
        "query_taxpayer": "T119",           # Query Taxpayer by TIN
        "get_branches": "T138",             # Get all branches
        
        # Stock Management
        "query_commodity_category": "T124", # Query commodity category
        "query_excise_duty": "T125",        # Query excise duty codes
        "get_exchange_rates": "T126",       # Get exchange rates
        "goods_upload": "T130",             # Goods upload (mandatory)
        "goods_inquiry": "T127",            # Goods/services inquiry
        "query_stock": "T128",              # Query stock quantity
        "stock_maintain": "T131",           # Stock maintain (in/out)
        "stock_transfer": "T139",           # Stock transfer between branches
        
        # Invoice Management ⭐ Most Critical
        "billing_upload": "T109",           # Billing upload (fiscalise)
        "batch_invoice_upload": "T129",     # Batch invoice upload
        "invoice_details": "T108",          # Invoice details (verify by FDN)
        "invoice_query": "T107",            # Invoice/receipt query
        "check_taxpayer_type": "T137",      # Check taxpayer type (VAT exemption)
        
        # Credit/Debit Notes (B2B/B2G only)
        "credit_application": "T110",       # Credit application (requires approval)
        "credit_note_status": "T111",       # Credit note status query
        "credit_note_cancel": "T114",       # Cancel approved credit note
        "query_credit_application": "T118", # Query credit application details
        "credit_application_detail": "T113",# Credit application detail
        
        # Item Query
        "query_goods_by_code": "T144",      # Query goods by code
    }
    
    def __init__(self, config: Dict[str, Any], key_client: "KeyClient"):
        self.config = config
        self.key_client = key_client
        self.timeout = config.get("http", {}).get("timeout", 30)
        
    def _get_endpoint_url(self) -> str:
        env = self.config.get("env", "sbx")
        return (
            "https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation"
            if env == "sbx"
            else "https://efrisws.ura.go.ug/ws/taapp/getInformation"
        ).strip()
    
    def _send(
        self,
        interface_key: str,
        payload: Dict[str, Any],
        encrypt: bool = True
    ) -> Dict[str, Any]:
        """
        Send encrypted request to EFRIS API per URA v1.5.
        
        Args:
            interface_key: Key from INTERFACES dict (e.g., "billing_upload")
            payload: Business payload (will be encrypted+signed if encrypt=True)
            encrypt: Whether to encrypt+sign (default True; False for T101/T104)
        """
        if interface_key not in self.INTERFACES:
            raise ApiException(
                f"Interface [{interface_key}] not configured",
                status_code=400
            )
        
        interface_code = self.INTERFACES[interface_key]
        
        # Get AES key (auto-fetches via T104 if needed)
        aes_key = self.key_client.fetch_aes_key() if encrypt else None
        
        # Build request envelope
        if encrypt and aes_key:
            request_envelope = build_encrypted_request(
                content=payload,
                aes_key=aes_key,
                interface_code=interface_code,
                tin=self.config["tin"],
                device_no=self.config["device_no"],
                brn=self.config.get("brn", ""),
                private_key=self.key_client._load_private_key()
            )
        else:
            # Unencrypted request (e.g., T101, T104 initial call)
            request_envelope = build_unencrypted_request(
                content=payload,
                interface_code=interface_code,
                tin=self.config["tin"],
                device_no=self.config["device_no"],
                brn=self.config.get("brn", "")
            )
        
        # Send HTTP POST (no headers per URA v1.5, page 4)
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
        
        # Parse + unwrap response
        try:
            resp_json = response.json()
        except json.JSONDecodeError as e:
            raise ApiException(f"Invalid JSON response: {e}", status_code=500)
        
        # Decrypt + validate response (if encrypted)
        if encrypt and aes_key:
            return unwrap_response(resp_json, aes_key)
        
        return resp_json
    
    def get(self, interface_key: str, params: Optional[Dict] = None) -> Dict:
        """GET-style call (rarely used in EFRIS; most are POST)"""
        return self._send(interface_key, params or {}, encrypt=True)
    
    def post(self, interface_key: str, data: Optional[Dict] = None) -> Dict:
        """POST-style call (standard for EFRIS)"""
        return self._send(interface_key, data or {}, encrypt=True)