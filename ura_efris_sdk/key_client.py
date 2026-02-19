import os
import time
import json
import base64
import requests
from datetime import datetime
from typing import Optional, Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

from .utils import build_unencrypted_request
from .exceptions import AuthenticationException, ApiException, EncryptionException


class KeyClient:
    """
    Manages RSA private key + AES key lifecycle per URA v1.5 spec.
    Matches working Frappe implementation logic.
    """

    T104_ENDPOINT_TEST = "https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation"
    T104_ENDPOINT_PROD = "https://efrisws.ura.go.ug/ws/taapp/getInformation"

    def __init__(
        self,
        pfx_path: str,
        password: str,
        tin: str,
        device_no: str,
        brn: str = "",
        sandbox: bool = True,
        timeout: int = 30
    ):
        self.pfx_path = pfx_path
        self.password = password  # plaintext from env
        self.tin = tin
        self.device_no = device_no
        self.brn = brn
        self.sandbox = sandbox
        self.timeout = timeout

        self._private_key: Optional[Any] = None
        self._aes_key: Optional[bytes] = None
        self._aes_key_fetched_at: Optional[float] = None
        self._aes_key_ttl_seconds = 24 * 60 * 60  # 24h

    def _get_endpoint(self) -> str:
        return self.T104_ENDPOINT_TEST if self.sandbox else self.T104_ENDPOINT_PROD

    def _load_private_key(self) -> Any:
        """Load RSA private key from .pfx (cached)"""
        if self._private_key is None:
            if not os.path.exists(self.pfx_path):
                raise AuthenticationException(f"PFX file not found: {self.pfx_path}")

            with open(self.pfx_path, "rb") as f:
                pfx_data = f.read()

            try:
                private_key, _, _ = pkcs12.load_key_and_certificates(
                    pfx_data,
                    self.password.encode() if self.password else b"",
                    backend=default_backend()
                )
            except Exception as e:
                raise AuthenticationException(f"Failed to load PFX: {e}")

            if private_key is None:
                raise AuthenticationException("Private key extraction failed")

            self._private_key = private_key

        return self._private_key

    def fetch_aes_key(self, force: bool = False) -> bytes:
        """
        Fetch AES key via T104 interface (URA v1.5).
        """

        # Return cached AES key if still valid
        if not force and self._aes_key and self._aes_key_fetched_at:
            if time.time() - self._aes_key_fetched_at < self._aes_key_ttl_seconds:
                return self._aes_key

        private_key = self._load_private_key()

        payload = build_unencrypted_request(
            content={},
            interface_code="T104",
            tin=self.tin,
            device_no=self.device_no,
            brn=self.brn
        )

        url = self._get_endpoint()

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
        except requests.RequestException as e:
            raise ApiException(f"T104 connection error: {e}")

        if response.status_code != 200:
            raise ApiException(
                f"T104 HTTP {response.status_code}: {response.text}",
                status_code=response.status_code
            )

        resp_json = response.json()

        return_state = resp_json.get("returnStateInfo", {})
        if return_state.get("returnMessage") != "SUCCESS":
            raise ApiException(
                f"T104 failed: {return_state.get('returnMessage')}",
                error_code=return_state.get("returnCode")
            )

        try:
            content_b64 = resp_json["data"]["content"]
            content_json = json.loads(base64.b64decode(content_b64).decode())

            encrypted_aes_b64 = (
                content_json.get("passowrdDes")  # URA typo
                or content_json.get("passwordDes")
            )

            if not encrypted_aes_b64:
                raise EncryptionException("Missing AES key field in T104 response")

            encrypted_aes = base64.b64decode(encrypted_aes_b64)

            print("Encrypted AES length:", len(encrypted_aes))

            # Convert private key → PEM → RSA key
            pkey_str = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            cipher = PKCS1_v1_5.new(RSA.import_key(pkey_str))

            # SAFE decrypt with sentinel
            aes_key_encrypted = cipher.decrypt(encrypted_aes, b"")

            if not aes_key_encrypted:
                raise EncryptionException(
                    "RSA decrypt failed — wrong certificate/password/device"
                )

            try:
                aes_key = base64.b64decode(aes_key_encrypted)
            except Exception:
                raise EncryptionException("Failed to base64-decode AES key")

            if len(aes_key) not in (16, 24, 32):
                raise EncryptionException(
                    f"Invalid AES key length: {len(aes_key)} bytes"
                )

            self._aes_key = aes_key
            self._aes_key_fetched_at = time.time()

            print("AES key length:", len(aes_key))

            return aes_key

        except Exception as e:
            raise AuthenticationException(f"Failed to extract AES key: {e}")

    def sign_payload(self, data: bytes) -> str:
        """Sign payload with RSA-SHA1"""
        private_key = self._load_private_key()
        from .utils import sign_rsa_sha1
        return sign_rsa_sha1(data, private_key)

    def forget_aes_key(self):
        """Clear cached AES key"""
        self._aes_key = None
        self._aes_key_fetched_at = None

    @property
    def aes_key_valid_until(self) -> Optional[str]:
        """Return AES expiry time"""
        if not self._aes_key_fetched_at:
            return None

        expiry = self._aes_key_fetched_at + self._aes_key_ttl_seconds
        return datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
