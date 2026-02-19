import os
from decimal import Decimal
from ura_efris_sdk import (
    Client,
    KeyClient,
    load_config_from_env,
    validate_config
)

# Load config
config = load_config_from_env(prefix="EFRIS")
validate_config(config)

password = config["pfx_password"]
if isinstance(password, bytes):
    password = password.decode()

# Initialize clients
key_client = KeyClient(
    pfx_path=config["pfx_path"],
    password=password,
    tin=config["tin"],
    device_no=config["device_no"],
    brn=config.get("brn", ""),
    sandbox=config["env"] == "sbx"
)

client = Client(config=config, key_client=key_client)

# Test connection (T101)
print("Testing connection...")
response = client.test_interface()
print(f"Server time: {response}")

# DEBUG: Force AES key fetch
print("\n[DEBUG] Fetching AES key...")
aes_key = key_client.fetch_aes_key(force=True)
print(f"[DEBUG] ✅ AES key: {len(aes_key)} bytes")
print(f"[DEBUG] AES key (hex): {aes_key.hex()}")

