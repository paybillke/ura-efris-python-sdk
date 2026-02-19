import os
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
    sandbox=config["env"] == "sbx"
)

client = Client(config=config, key_client=key_client)

# Test connection (T101)
print("Testing connection...")
response = client.test_interface()
print(f"Server time: {response}")

# Fiscalise invoice (T109)
print("Fiscalising invoice...")
invoice_payload = {
    "invoiceType": "0",
    "invoiceNo": "INV-2024-001",
    "invoiceDate": "20240219",
    "buyerType": "1",
    "sellerTin": config["tin"],
    "sellerBranchNo": "01",
    "currency": "UGX",
    "goodsDetails": [{
        "goodsCode": "SUGAR-001",
        "goodsName": "White Sugar 1kg",
        "unit": "KG",
        "qty": 2,
        "unitPrice": 3500,
        "amount": 7000,
        "taxRate": 18,
        "taxAmount": 1067.80,
        "discountFlag": "0"
    }],
    "totalAmount": 7000,
    "totalTaxAmount": 1067.80,
    "operatorName": "admin"
}

response = client.fiscalise_invoice(invoice_payload)
content = response.get("data", {}).get("content", {})
print(f"FDN: {content.get('invoiceNo')}")
print(f"QR Code: {content.get('qrCode')}")