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


# =========================================================
# TIME UTILS (UTC+3 - East Africa Time per URA spec)
# =========================================================

def get_uganda_timestamp() -> str:
    """Returns current time in UTC+3 format: YYYY-MM-DD HH:MM:SS"""
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_uganda_timestamp_ddmmyyyy() -> str:
    """Returns current time in DD/MM/YYYY HH:MM:SS format (for receipts)"""
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%d/%m/%Y %H:%M:%S")


def get_uganda_date_yyyymmdd() -> str:
    """Returns current date in YYYYMMDD format"""
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%Y%m%d")


def validate_time_sync(client_time: str, server_time: str, tolerance_minutes: int = 10) -> bool:
    """Validate client/server time difference is within tolerance (URA: ±10 min)"""
    fmt = "%Y-%m-%d %H:%M:%S"
    try:
        client_dt = datetime.strptime(client_time, fmt)
        server_dt = datetime.strptime(server_time, fmt)
        diff_seconds = abs((server_dt - client_dt).total_seconds())
        return diff_seconds <= (tolerance_minutes * 60)
    except ValueError:
        return False


# =========================================================
# AES ENCRYPTION (ECB Mode) - MATCHES FRAPPE LOGIC EXACTLY
# =========================================================

def encrypt_aes_ecb(plaintext: str, key: bytes) -> str:
    """
    Encrypt with AES-ECB, manual PKCS7 padding.
    Matches Frappe's encryption_utils.encrypt_aes_ecb() exactly.
    Returns base64 string.
    """
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES key must be 16, 24, or 32 bytes")
    
    # Manual PKCS7 padding - matches Frappe exactly
    padding_length = 16 - (len(plaintext) % 16)
    padding = bytes([padding_length] * padding_length)
    
    # Frappe style: concatenate string + decoded padding, then encode
    padded_data = plaintext + padding.decode("utf-8", errors="ignore")
    
    cipher = AES.new(key, AES.MODE_ECB)
    ct_bytes = cipher.encrypt(padded_data.encode("utf-8"))
    return base64.b64encode(ct_bytes).decode("utf-8")


def decrypt_aes_ecb(ciphertext_b64: str, key: bytes) -> str:
    """
    Decrypt base64 AES-ECB ciphertext, manual unpadding.
    Matches Frappe's encryption_utils.decrypt_aes_ecb() exactly.
    Returns plaintext string.
    """
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES key must be 16, 24, or 32 bytes")
    
    ciphertext = base64.b64decode(ciphertext_b64)
    cipher = AES.new(key, AES.MODE_ECB)
    
    # Decrypt and decode to string (matches Frappe)
    plaintext_with_padding = cipher.decrypt(ciphertext).decode("utf-8", errors="ignore")
    
    # Manual PKCS7 unpadding - matches Frappe exactly
    padding_length = ord(plaintext_with_padding[-1])
    return plaintext_with_padding[:-padding_length]


# =========================================================
# RSA SIGNING (SHA1withRSA) - MATCHES FRAPPE LOGIC
# =========================================================

def load_private_key_from_pfx(pfx_data: bytes, password: str) -> Any:
    """Load RSA private key from PKCS#12 (.pfx) file - matches Frappe"""
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
    Sign data with RSA-SHA1 (URA requirement).
    CRITICAL: Input should be the base64-encoded encrypted content as bytes.
    Matches Frappe's sign_data() exactly.
    """
    try:
        signature = private_key.sign(
            data,
            asym_padding.PKCS1v15(),  # PKCS1v15 (no underscore)
            hashes.SHA1()  # Must be SHA1 per URA v1.5
        )
        return base64.b64encode(signature).decode("utf-8")
    except Exception as e:
        raise EncryptionException(f"RSA-SHA1 signing failed: {e}")


def decrypt_rsa_pkcs1(encrypted_data: bytes, private_key: Any) -> bytes:
    """Decrypt RSA-PKCS#1 v1.5 encrypted data (for T104 AES key)"""
    try:
        return private_key.decrypt(
            encrypted_data,
            asym_padding.PKCS1v15()
        )
    except Exception as e:
        raise EncryptionException(f"RSA decryption failed: {e}")


# =========================================================
# REQUEST/RESPONSE ENVELOPE BUILDERS
# =========================================================

def build_global_info(
    interface_code: str,
    tin: str,
    device_no: str,
    brn: str = "",
    user: str = "admin",
    longitude: str = "32.5825",
    latitude: str = "0.3476"
) -> dict:
    """Build globalInfo section - matches Frappe fetch_data()"""
    return {
        "appId": "AP04",
        "version": "1.1.20191201",
        "dataExchangeId": uuid.uuid4().hex.upper(),
        "interfaceCode": interface_code,
        "requestCode": "TP",
        "requestTime": get_uganda_timestamp(),
        "responseCode": "TA",
        "userName": user,
        "deviceMAC": "FFFFFFFFFFFF",
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
    Build encrypted+signed request envelope.
    CRITICAL: Signature calculation matches Frappe's encrypt_and_prepare_data().
    """
    # 1. Serialize + encrypt content
    json_content = json.dumps(content, separators=(',', ':'), ensure_ascii=False)
    encrypted_content = encrypt_aes_ecb(json_content, aes_key)  # Returns base64 string
    
    # 2. 🔧 CRITICAL: Sign the base64-encoded encrypted content (as bytes)
    # Matches Frappe: sign_data(private_key, newEncrypteddata.encode())
    # where newEncrypteddata = base64.b64encode(isAESEncrypted).decode("utf-8")
    signature = sign_rsa_sha1(encrypted_content.encode('utf-8'), private_key)
    
    # 3. Build envelope
    return {
        "data": {
            "content": encrypted_content,  # Base64 string
            "signature": signature,         # Base64 signature
            "dataDescription": {
                "codeType": "1",    # Encrypted
                "encryptCode": "2", # AES
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
    """Build unencrypted request envelope (for T101, T104)"""
    return {
        "data": {
            "content": "",
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
    """Decrypt + validate EFRIS response - matches Frappe logic"""
    # 1. Check returnStateInfo (URA v1.5, page 27)
    return_state = response_json.get("returnStateInfo", {})
    if return_state.get("returnMessage") != "SUCCESS":
        from .exceptions import ApiException
        raise ApiException(
            message=return_state.get("returnMessage", "Unknown error"),
            error_code=return_state.get("returnCode"),
            status_code=400
        )
    
    # 2. Decrypt content if present and aes_key provided
    data_section = response_json.get("data", {})
    encrypted_content = data_section.get("content")
    
    if encrypted_content and aes_key:
        try:
            decrypted = decrypt_aes_ecb(encrypted_content, aes_key)
            response_json["data"]["content"] = json.loads(decrypted)
        except Exception as e:
            from .exceptions import EncryptionException
            raise EncryptionException(f"Response decryption failed: {e}")
    
    return response_json