import base64
import json
import hashlib
from datetime import datetime
from typing import Union, Optional, Any, Dict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.hazmat.primitives import hashes, serialization
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
# AES ENCRYPTION (ECB Mode - per URA samples)
# =========================================================

def encrypt_aes_ecb(plaintext: str, key: bytes) -> str:
    """Encrypt with AES-ECB, PKCS7 padding, return base64 string"""
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES key must be 16, 24, or 32 bytes")
    
    cipher = AES.new(key, AES.MODE_ECB)
    padded = pad(plaintext.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_aes_ecb(ciphertext_b64: str, key: bytes) -> str:
    """Decrypt base64 AES-ECB ciphertext, return plaintext string"""
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES key must be 16, 24, or 32 bytes")
    
    ciphertext = base64.b64decode(ciphertext_b64)
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_padded = cipher.decrypt(ciphertext)
    plaintext = unpad(decrypted_padded, AES.block_size)
    return plaintext.decode("utf-8")


# =========================================================
# RSA SIGNING (SHA1withRSA - URA Requirement per v1.5)
# =========================================================

def load_private_key_from_pfx(pfx_data: bytes, password: str) -> Any:
    """Load RSA private key from PKCS#12 (.pfx) file with password"""
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
    """Sign data with RSA-SHA1 (URA requirement), return base64 signature"""
    try:
        signature = private_key.sign(
            data,
            asym_padding.PKCS1v15(),  # ✅ CORRECT: PKCS1v15 (no underscore)
            hashes.SHA1()  # ✅ Must be SHA1, not SHA256 (per URA v1.5)
        )
        return base64.b64encode(signature).decode("utf-8")
    except Exception as e:
        raise EncryptionException(f"RSA-SHA1 signing failed: {e}")


def decrypt_rsa_pkcs1(encrypted_data: bytes, private_key: Any) -> bytes:
    """Decrypt RSA-PKCS#1 v1.5 encrypted data (for T104 AES key)"""
    try:
        return private_key.decrypt(
            encrypted_data,
            asym_padding.PKCS1v15()  # ✅ CORRECT: PKCS1v15 (no underscore)
        )
    except Exception as e:
        raise EncryptionException(f"RSA decryption failed: {e}")


# =========================================================
# REQUEST/RESPONSE ENVELOPE BUILDERS (per URA v1.5 spec)
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
    """Build globalInfo section per URA v1.5 spec (page 9)"""
    return {
        "appId": "AP04",  # Fixed for system-to-system (URA v1.5, page 9)
        "version": "1.1.20191201",
        "dataExchangeId": uuid.uuid4().hex.upper(),
        "interfaceCode": interface_code,
        "requestCode": "TP",
        "requestTime": get_uganda_timestamp(),  # UTC+3 (URA v1.5, page 9)
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
    """Build full encrypted+signed request envelope per URA v1.5 (page 7-8)"""
    # 1. Serialize + encrypt content
    json_content = json.dumps(content, separators=(',', ':'), ensure_ascii=False)
    encrypted_content = encrypt_aes_ecb(json_content, aes_key)
    
    # 2. Sign the encrypted content (per spec: Signature = Sign(Encrypted(Content)))
    signature = sign_rsa_sha1(base64.b64decode(encrypted_content), private_key)
    
    # 3. Build envelope (data + globalInfo + returnStateInfo)
    return {
        "data": {
            "content": encrypted_content,
            "signature": signature,
            "dataDescription": {
                "codeType": "1",    # Encrypted (URA v1.5, page 7)
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
    """Build unencrypted request envelope (for T101, T104 initial call)"""
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
    """Decrypt + validate EFRIS response per URA v1.5 (page 15-16)"""
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