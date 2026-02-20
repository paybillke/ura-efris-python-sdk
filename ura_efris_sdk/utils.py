"""
EFRIS Utility Functions
Handles encryption, decryption, signing, and timestamp operations.
All cryptographic operations follow URA EFRIS API specifications.
"""
import base64
import json
from datetime import datetime
from typing import Union, Optional, Any, Dict
from Crypto.Cipher import AES
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
import pytz
import uuid
from .exceptions import EncryptionException, AuthenticationException


# =============================================================================
# TIMESTAMP UTILITIES
# =============================================================================

def get_uganda_timestamp() -> str:
    """
    Get current timestamp in Uganda timezone (Africa/Kampala).
    Format: yyyy-MM-dd HH:mm:ss (used for requests)
    
    Returns:
        str: Formatted timestamp string
    """
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_uganda_timestamp_ddmmyyyy() -> str:
    """
    Get current timestamp in Uganda timezone with DD/MM/YYYY format.
    Format: dd/MM/yyyy HH:mm:ss (used for responses)
    
    Returns:
        str: Formatted timestamp string
    """
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%d/%m/%Y %H:%M:%S")


def get_uganda_date_yyyymmdd() -> str:
    """
    Get current date in Uganda timezone.
    Format: YYYYMMDD
    
    Returns:
        str: Formatted date string
    """
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%Y%m%d")


def validate_time_sync(
    client_time: str,
    server_time: str,
    tolerance_minutes: int = 10
) -> bool:
    """
    Validate that client and server times are synchronized.
    EFRIS requires time difference to be within 10 minutes.
    
    Args:
        client_time: Client timestamp (yyyy-MM-dd HH:mm:ss)
        server_time: Server timestamp (yyyy-MM-dd HH:mm:ss)
        tolerance_minutes: Maximum allowed difference in minutes
    
    Returns:
        bool: True if times are synchronized within tolerance
    """
    fmt = "%Y-%m-%d %H:%M:%S"
    try:
        client_dt = datetime.strptime(client_time, fmt)
        server_dt = datetime.strptime(server_time, fmt)
        diff_seconds = abs((server_dt - client_dt).total_seconds())
        return diff_seconds <= (tolerance_minutes * 60)
    except ValueError:
        return False


# =============================================================================
# AES ENCRYPTION/DECRYPTION (ECB Mode)
# =============================================================================

def encrypt_aes_ecb(plaintext: str, key: bytes) -> str:
    """
    Encrypt plaintext using AES-ECB mode with PKCS7 padding.
    
    Args:
        plaintext: String to encrypt
        key: AES key (must be 16, 24, or 32 bytes)
    
    Returns:
        str: Base64-encoded ciphertext
    
    Raises:
        ValueError: If key length is invalid
    """
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES key must be 16, 24, or 32 bytes")
    
    plaintext_bytes = plaintext.encode("utf-8")
    # Apply PKCS7 padding
    padding_length = 16 - (len(plaintext_bytes) % 16)
    padding = bytes([padding_length] * padding_length)
    padded_data = plaintext_bytes + padding
    
    cipher = AES.new(key, AES.MODE_ECB)
    ct_bytes = cipher.encrypt(padded_data)
    return base64.b64encode(ct_bytes).decode("utf-8")


def decrypt_aes_ecb(ciphertext_b64: str, key: bytes) -> str:
    """
    Decrypt ciphertext using AES-ECB mode with PKCS7 padding validation.
    
    Args:
        ciphertext_b64: Base64-encoded ciphertext
        key: AES key (must be 16, 24, or 32 bytes)
    
    Returns:
        str: Decrypted plaintext
    
    Raises:
        EncryptionException: If padding validation fails
    """
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES key must be 16, 24, or 32 bytes")
    
    ciphertext = base64.b64decode(ciphertext_b64)
    cipher = AES.new(key, AES.MODE_ECB)
    padded_plaintext = cipher.decrypt(ciphertext)
    
    # Validate and remove PKCS7 padding
    padding_length = padded_plaintext[-1]
    if padding_length > 16 or padding_length == 0:
        raise EncryptionException("Invalid PKCS7 padding")
    if not all(b == padding_length for b in padded_plaintext[-padding_length:]):
        raise EncryptionException("PKCS7 padding verification failed")
    
    plaintext_bytes = padded_plaintext[:-padding_length]
    return plaintext_bytes.decode("utf-8", errors="ignore")


def _encrypt_aes_ecb_raw(plaintext_bytes: bytes, key: bytes) -> bytes:
    """
    Low-level AES-ECB encryption returning raw bytes (for signing).
    Used internally to encrypt content before creating signature.
    
    Args:
        plaintext_bytes: Raw bytes to encrypt
        key: AES key
    
    Returns:
        bytes: Encrypted raw bytes (not base64 encoded)
    """
    padding_length = 16 - (len(plaintext_bytes) % 16)
    padding = bytes([padding_length] * padding_length)
    padded = plaintext_bytes + padding
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(padded)


# =============================================================================
# RSA OPERATIONS
# =============================================================================

def load_private_key_from_pfx(pfx_data: bytes, password: str) -> Any:
    """
    Extract private key from PFX/PKCS12 file.
    
    Args:
        pfx_data: Raw PFX file content
        password: PFX password
    
    Returns:
        Private key object
    
    Raises:
        EncryptionException: If key extraction fails
    """
    try:
        private_key, _, _ = pkcs12.load_key_and_certificates(
            pfx_data,
            password.encode() if password else b"",
            backend=default_backend()
        )
        if private_key is None:
            raise ValueError("Failed to extract private key from .pfx")
        return private_key
    except Exception as e:
        raise EncryptionException(f"Failed to load private key: {e}")


def sign_rsa_sha1(data: bytes, private_key: Any) -> str:
    """
    Sign data using RSA-SHA1 algorithm (required by EFRIS API).
    
    Args:
        data: Data bytes to sign
        private_key: RSA private key object
    
    Returns:
        str: Base64-encoded signature
    
    Raises:
        EncryptionException: If signing fails
    """
    try:
        signature = private_key.sign(
            data,
            asym_padding.PKCS1v15(),  # PKCS#1 v1.5 padding
            hashes.SHA1()  # SHA-1 hash (EFRIS requirement)
        )
        return base64.b64encode(signature).decode("utf-8")
    except Exception as e:
        raise EncryptionException(f"RSA-SHA1 signing failed: {e}")


def decrypt_rsa_pkcs1(encrypted_data: bytes, private_key: Any) -> bytes:
    """
    Decrypt data using RSA-PKCS1 v1.5 padding.
    
    Args:
        encrypted_data: Encrypted bytes
        private_key: RSA private key object
    
    Returns:
        bytes: Decrypted data
    
    Raises:
        EncryptionException: If decryption fails
    """
    try:
        return private_key.decrypt(
            encrypted_data,
            asym_padding.PKCS1v15()
        )
    except Exception as e:
        raise EncryptionException(f"RSA decryption failed: {e}")


# =============================================================================
# REQUEST BUILDING
# =============================================================================

def build_global_info(
    interface_code: str,
    tin: str,
    device_no: str,
    brn: str = "",
    user: str = "admin",
    longitude: str = "32.5825",
    latitude: str = "0.3476"
) -> dict:
    """
    Build the globalInfo section of EFRIS API requests.
    Contains metadata required for all API calls.
    
    Args:
        interface_code: API interface code (e.g., "T109")
        tin: Taxpayer Identification Number
        device_no: Device serial number
        brn: Business Registration Number (optional)
        user: Username for the request
        longitude: GPS longitude
        latitude: GPS latitude
    
    Returns:
        dict: Global info dictionary
    """
    return {
        "appId": "AP04",  # System-to-System integration
        "version": "1.1.20191201",  # API version
        "dataExchangeId": uuid.uuid4().hex.upper(),  # Unique request ID
        "interfaceCode": interface_code,
        "requestCode": "TP",  # Taxpayer side
        "requestTime": get_uganda_timestamp(),
        "responseCode": "TA",  # URA side
        "userName": user,
        "deviceMAC": "FFFFFFFFFFFF",  # Default MAC for system integration
        "deviceNo": device_no,
        "tin": tin,
        "brn": brn,
        "taxpayerID": "1",
        "longitude": longitude,
        "latitude": latitude,
        "agentType": "0",
        "extendField": {
            "responseDateFormat": "dd/MM/yyyy",
            "responseTimeFormat": "dd/MM/yyyy HH:mm:ss",
            "referenceNo": "",
            "operatorName": user,
            "offlineInvoiceException": {
                "errorCode": "",
                "errorMsg": ""
            }
        }
    }


def build_encrypted_request(
    content: dict,
    aes_key: bytes,
    interface_code: str,
    tin: str,
    device_no: str,
    brn: str,
    private_key: Any
) -> dict:
    """
    Build an encrypted EFRIS API request envelope.
    
    Structure:
    {
        "data": {
            "content": "<base64 encrypted JSON>",
            "signature": "<base64 RSA signature>",
            "dataDescription": {
                "codeType": "1",      # Encrypted
                "encryptCode": "2",   # AES
                "zipCode": "0"        # No compression
            }
        },
        "globalInfo": {...},
        "returnStateInfo": {...}
    }
    
    Args:
        content: Request payload dictionary
        aes_key: AES encryption key
        interface_code: API interface code
        tin: Taxpayer ID
        device_no: Device number
        brn: Business Registration Number
        private_key: RSA private key for signing
    
    Returns:
        dict: Complete request envelope
    """
    # Serialize content to compact JSON
    json_content = json.dumps(content, separators=(',', ':'), ensure_ascii=False)
    
    # Encrypt content with AES
    encrypted_bytes = _encrypt_aes_ecb_raw(json_content.encode("utf-8"), aes_key)
    encrypted_content_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")
    
    # Sign the encrypted bytes (not the base64)
    signature = sign_rsa_sha1(encrypted_bytes, private_key)
    
    return {
        "data": {
            "content": encrypted_content_b64,
            "signature": signature,
            "dataDescription": {
                "codeType": "1",    # Encrypted
                "encryptCode": "2", # AES encryption
                "zipCode": "0"      # No compression
            }
        },
        "globalInfo": build_global_info(interface_code, tin, device_no, brn),
        "returnStateInfo": {
            "returnCode": "",
            "returnMessage": ""
        }
    }


def build_unencrypted_request(
    content: dict,
    interface_code: str,
    tin: str,
    device_no: str,
    brn: str = ""
) -> dict:
    """
    Build an unencrypted EFRIS API request envelope.
    Used for initialization endpoints (T101, T102, T103, T104).
    
    Args:
        content: Request payload dictionary
        interface_code: API interface code
        tin: Taxpayer ID
        device_no: Device number
        brn: Business Registration Number
    
    Returns:
        dict: Complete request envelope
    """
    return {
        "data": {
            "content": "",  # Empty for unencrypted requests
            "signature": "",
            "dataDescription": {
                "codeType": "0",  # Not encrypted
                "encryptCode": "1",
                "zipCode": "0"
            }
        },
        "globalInfo": build_global_info(interface_code, tin, device_no, brn),
        "returnStateInfo": {
            "returnCode": "",
            "returnMessage": ""
        }
    }


def unwrap_response(response_json: dict, aes_key: Optional[bytes] = None) -> dict:
    """
    Process and decrypt EFRIS API response.
    Validates return codes and decrypts content if encrypted.
    
    Args:
        response_json: Raw API response dictionary
        aes_key: AES key for decryption (if response is encrypted)
    
    Returns:
        dict: Processed response with decrypted content
    
    Raises:
        ApiException: If returnCode indicates error
        EncryptionException: If decryption fails
    """
    return_state = response_json.get("returnStateInfo", {})
    return_code = return_state.get("returnCode", "")
    return_msg = return_state.get("returnMessage", "")
    
    # Check for API-level errors
    # Note: returnCode "00" = SUCCESS, "99" = Unknown error
    if return_code == "99" or return_msg != "SUCCESS":
        from .exceptions import ApiException
        raise ApiException(
            message=return_msg or "Unknown API error",
            error_code=return_code or "99",
            status_code=400,
            details={"returnStateInfo": return_state}
        )
    
    # Decrypt content if encrypted
    data_section = response_json.get("data", {})
    encrypted_content = data_section.get("content")
    if encrypted_content and aes_key:
        try:
            decrypted_json = decrypt_aes_ecb(encrypted_content, aes_key)
            response_json["data"]["content"] = json.loads(decrypted_json)
        except Exception as e:
            from .exceptions import EncryptionException
            raise EncryptionException(
                f"Response decryption failed: {e}",
                details={"encrypted_content_preview": encrypted_content[:100] + "..."}
            )
    
    return response_json