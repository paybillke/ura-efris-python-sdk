"""
EFRIS Utility Functions
Handles encryption, decryption, signing, and timestamp operations.
All cryptographic operations follow URA EFRIS API specifications.
"""
import base64
import json
import logging
import base64
import gzip
from io import BytesIO
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

logger = logging.getLogger(__name__)


# =============================================================================
# TIMESTAMP UTILITIES
# =============================================================================

def get_uganda_timestamp() -> str:
    """
    Get current timestamp in Uganda timezone (Africa/Kampala).
    Format: yyyy-MM-dd HH:mm:ss (used for requests)
    """
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_uganda_timestamp_ddmmyyyy() -> str:
    """
    Get current timestamp in Uganda timezone with DD/MM/YYYY format.
    Format: dd/MM/yyyy HH:mm:ss (used for responses)
    """
    ug_tz = pytz.timezone("Africa/Kampala")
    now = datetime.now(ug_tz)
    return now.strftime("%d/%m/%Y %H:%M:%S")


def get_uganda_date_yyyymmdd() -> str:
    """Get current date in Uganda timezone. Format: YYYYMMDD"""
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
    Handles both yyyy-MM-dd and dd/MM/yyyy formats.
    """
    formats = ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
    
    try:
        # Try parsing client time
        client_dt = None
        for fmt in formats:
            try:
                client_dt = datetime.strptime(client_time, fmt)
                break
            except ValueError:
                continue
        if client_dt is None:
            return False
            
        # Try parsing server time
        server_dt = None
        for fmt in formats:
            try:
                server_dt = datetime.strptime(server_time, fmt)
                break
            except ValueError:
                continue
        if server_dt is None:
            return False
        
        diff_seconds = abs((server_dt - client_dt).total_seconds())
        return diff_seconds <= (tolerance_minutes * 60)
    except Exception:
        return False
        

# =============================================================================
# AES ENCRYPTION/DECRYPTION (ECB Mode)
# =============================================================================

def encrypt_aes_ecb(plaintext: str, key: bytes) -> str:
    """Encrypt plaintext using AES-ECB mode with PKCS7 padding."""
    if len(key) not in [16, 24, 32]:
        raise ValueError("AES key must be 16, 24, or 32 bytes")
    
    plaintext_bytes = plaintext.encode("utf-8")
    padding_length = 16 - (len(plaintext_bytes) % 16)
    padding = bytes([padding_length] * padding_length)
    padded_data = plaintext_bytes + padding
    
    cipher = AES.new(key, AES.MODE_ECB)
    ct_bytes = cipher.encrypt(padded_data)
    return base64.b64encode(ct_bytes).decode("utf-8")


def decrypt_aes_ecb(
    ciphertext_b64: str,
    key: bytes = None,
    encrypt_code: str = "2",
    zip_code: str = "0"
) -> str:
    if not ciphertext_b64:
        return None

    print(f"Decrypting AES-ECB content: encryptCode={encrypt_code}, zipCode={zip_code}")

    # ---------------------------------------------------------
    # STEP 1 — Base64 decode (EFRIS always encodes content)
    # ---------------------------------------------------------
    try:
        data_bytes = base64.b64decode(ciphertext_b64)
    except Exception as e:
        raise EncryptionException(f"Base64 decode failed: {e}")

    # ---------------------------------------------------------
    # GZIP decompress AFTER decryption
    # ---------------------------------------------------------
    if zip_code == "1":
        try:
            if data_bytes[:2] != b"\x1f\x8b":
                raise EncryptionException("zipCode=1 but data not gzipped")

            data_bytes = gzip.decompress(data_bytes)
        except Exception as e:
            raise EncryptionException(f"GZIP decompression failed: {e}")

    # ---------------------------------------------------------
    # AES decrypt FIRST (when encryptCode=2)
    # ---------------------------------------------------------
    if encrypt_code == "2":
        if not key:
            raise EncryptionException("AES key required for encrypted content")

        if len(data_bytes) % 16 != 0:
            raise EncryptionException(
                f"Ciphertext length {len(data_bytes)} not multiple of 16"
            )

        try:
            cipher = AES.new(key, AES.MODE_ECB)
            padded_plaintext = cipher.decrypt(data_bytes)
        except Exception as e:
            raise EncryptionException(f"AES decryption failed: {e}")

        # -----------------------------------------------------
        # STEP 3 — PKCS7 unpadding
        # -----------------------------------------------------
        pad_len = padded_plaintext[-1]

        if pad_len < 1 or pad_len > 16:
            raise EncryptionException("Invalid PKCS7 padding")

        if padded_plaintext[-pad_len:] != bytes([pad_len]) * pad_len:
            raise EncryptionException("PKCS7 padding verification failed")

        data_bytes = padded_plaintext[:-pad_len]

    # ---------------------------------------------------------
    # UTF-8 decode
    # ---------------------------------------------------------
    try:
        return data_bytes.decode("utf-8")
    except Exception as e:
        raise EncryptionException(f"UTF-8 decode failed: {e}")

def decompress_gzip(data):
    try:
        decompressed_data = gzip.decompress(data)
        return decompressed_data.decode('utf-8')
    except Exception as e:
        print("Error Decompressing Gzip data:", e)
        return None
    
def _encrypt_aes_ecb_raw(plaintext_bytes: bytes, key: bytes) -> bytes:
    """
    Low-level AES-ECB encryption returning raw bytes (for signing).
    CRITICAL: This is what gets signed, NOT the base64-encoded version.
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
    """Extract private key from PFX/PKCS12 file."""
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
    CRITICAL: Sign the RAW encrypted bytes, NOT base64-encoded.
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
    """Decrypt data using RSA-PKCS1 v1.5 padding."""
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
    latitude: str = "0.3476",
    taxpayer_id: str = ""  # ← Make this configurable
) -> dict:
    """Build the globalInfo section of EFRIS API requests."""
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
        "taxpayerID": taxpayer_id if taxpayer_id else "1",  # ← Use dynamic value from sign-in if available
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
    private_key: Any,
    taxpayer_id: str = ""
) -> dict:
    """
    Build an encrypted EFRIS API request envelope.
    
    CORRECT FLOW (per EFRIS spec):
    1. Serialize content to compact JSON (no whitespace, sorted keys)
    2. Sign the RAW JSON bytes ← KEY FIX
    3. Base64 encode the JSON string for signature transport
    4. AES-ECB encrypt the RAW JSON bytes for the content field
    5. Base64-encode the encrypted bytes for transport
    """
    # 1. Serialize JSON (already correct)
    json_content = json.dumps(
        content,
        separators=(',', ':'),
        ensure_ascii=False,
        sort_keys=False
    )
    json_bytes = json_content.encode('utf-8')

    # 2. AES encrypt FIRST
    encrypted_bytes = _encrypt_aes_ecb_raw(json_bytes, aes_key)

    # 3. ✅ Sign ENCRYPTED bytes (CRITICAL FIX)
    encrypted_content_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
    signature = sign_rsa_sha1(encrypted_content_b64.encode(), private_key)

    return {
        "data": {
            "content": encrypted_content_b64,  # Base64 of AES-encrypted bytes
            "signature": signature,             # Base64 of RSA-SHA1 signature over RAW JSON
            "dataDescription": {
                "codeType": "1",
                "encryptCode": "2",
                "zipCode": "0"
            }
        },
        "globalInfo": build_global_info(interface_code, tin, device_no, brn, taxpayer_id),
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
    brn: str = "",
    taxpayer_id: str = ""
) -> dict:
    """
    Build an unencrypted EFRIS API request envelope.
    
    CRITICAL: Even unencrypted requests must Base64-encode the content field
    if the payload is not empty (per EFRIS spec).
    """
    # Base64 encode content if not empty
    content_b64 = ""
    if content:
        # Serialize to compact JSON (no whitespace)
        json_content = json.dumps(content, separators=(',', ':'), ensure_ascii=False)
        # Base64 encode for transport
        content_b64 = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
    
    return {
        "data": {
            "content": content_b64,  # Base64 encoded (or empty string)
            "signature": "",  # No signature for unencrypted requests
            "dataDescription": {
                "codeType": "0",  # Not encrypted
                "encryptCode": "1",  # RSA (unused when codeType=0)
                "zipCode": "0"  # No compression
            }
        },
        "globalInfo": build_global_info(interface_code, tin, device_no, brn, taxpayer_id),
        "returnStateInfo": {
            "returnCode": "",
            "returnMessage": ""
        }
    }


def unwrap_response(response_json: dict, aes_key: Optional[bytes] = None) -> dict:
    """
    Process EFRIS API response: Base64 decode + optional AES decrypt.
    
    CRITICAL: EFRIS always Base64-encodes data.content.
    - codeType="0": Base64 decode only (plain JSON)
    - codeType="1": Base64 decode + AES-ECB decrypt + PKCS7 unpad
    """
    from .exceptions import ApiException, EncryptionException
    
    return_state = response_json.get("returnStateInfo", {})
    return_code = return_state.get("returnCode", "")
    return_msg = return_state.get("returnMessage", "")
    
    logger.debug(f"Response returnCode: {return_code}, returnMessage: {return_msg}")
    
    # Check for API-level errors
    if return_code == "99" or (return_msg and return_msg != "SUCCESS"):
        raise ApiException(
            message=return_msg or "Unknown API error",
            error_code=return_code or "99",
            status_code=400,
            details={"returnStateInfo": return_state}
        )
    
    data_section = response_json.get("data", {})
    content_b64 = data_section.get("content", "")
    
    # Skip if no content
    if not content_b64:
        return response_json
    
    # Check codeType to determine processing
    data_desc = data_section.get("dataDescription", {})
    code_type = data_desc.get("codeType", "0")
    encrypt_code = data_desc.get("encryptCode", "0")
    zip_code = data_desc.get("zipCode", "0")
    print(f"Response codeType: {code_type}, encryptCode: {encrypt_code}, zipCode: {zip_code}")
    logger.debug(f"Response codeType: {code_type}, encryptCode: {encrypt_code}, zipCode: {zip_code}")
    
    try:
        if code_type == "1":
            # Encrypted: decrypt_aes_ecb handles Base64 decode + AES decrypt + unpad
            if not aes_key:
                raise EncryptionException("Encrypted response but no AES key provided")
            content_str = decrypt_aes_ecb(content_b64, aes_key, encrypt_code=encrypt_code, zip_code=zip_code)
            logger.debug(f"Decrypted content length: {len(content_str)} chars")
        else:
            # Plain text: just Base64 decode
            decoded_bytes = base64.b64decode(content_b64)
            content_str = decoded_bytes.decode('utf-8')
            logger.debug(f"Decoded content length: {len(content_str)} chars")
        
        # Parse JSON and inject into response
        decoded_content = json.loads(content_str)
        response_json["data"]["content"] = decoded_content
        
    except json.JSONDecodeError:
        # Fallback: keep as string if not valid JSON
        logger.warning("Response content is not valid JSON, keeping as string")
        response_json["data"]["content"] = content_str
    except Exception as e:
        logger.error(f"Response processing failed: {e}")
        raise EncryptionException(f"Response processing failed: {e}")
    
    return response_json