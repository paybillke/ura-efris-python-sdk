#!/usr/bin/env python3
"""
EFRIS API Complete Endpoint Integration Test
=============================================
This script tests ALL endpoints from the EFRIS API documentation (T101-T187).
It's designed for integration testing against the Uganda Revenue Authority EFRIS system.

Usage:
    export EFRIS_ENV=sbx
    export EFRIS_TIN=your_tin
    export EFRIS_DEVICE_NO=your_device
    export EFRIS_PFX_PATH=/path/to/cert.pfx
    export EFRIS_PFX_PASSWORD=your_password
    python test_all_endpoints.py
"""

import os
import sys
import json
import time
import uuid
import base64
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Union

from ura_efris_sdk import (
    Client,
    KeyClient,
    load_config_from_env,
    validate_config
)
from ura_efris_sdk.exceptions import APIException, ValidationException, EncryptionException


# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_endpoint(code: str, name: str):
    """Print endpoint information."""
    print(f"\n[{code}] {name}")
    print("-" * 60)


def print_response(response: Any, max_length: int = 500):
    """Print response with truncation for large payloads."""
    if isinstance(response, dict):
        response_str = json.dumps(response, indent=2, default=str)
    else:
        response_str = str(response)
    
    if len(response_str) > max_length:
        print(response_str[:max_length] + "... [truncated]")
    else:
        print(response_str)


def handle_error(endpoint: str, error: Exception):
    """Handle and print error information."""
    print(f"❌ ERROR: {type(error).__name__}")
    print(f"   Message: {str(error)}")
    exit(1)
    if hasattr(error, 'error_code'):
        print(f"   Error Code: {error.error_code}")
    if hasattr(error, 'details'):
        print(f"   Details: {error.details}")
    


def generate_uuid() -> str:
    """Generate a UUID for dataExchangeId."""
    return str(uuid.uuid4()).replace('-', '')[:32]


def get_timestamp() -> str:
    """Get current timestamp in required format."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_date_timestamp() -> str:
    """Get current date in required format."""
    return datetime.now().strftime('%Y-%m-%d')


# =============================================================================
# MAIN TEST CLASS
# =============================================================================

class EfrisEndpointTester:
    """Tests all EFRIS API endpoints according to documentation."""
    
    def __init__(self, client: Client, key_client: KeyClient, config: Dict[str, Any]):
        self.client = client
        self.key_client = key_client
        self.config = config
        self.results = {
            "passed": [],
            "failed": [],
            "skipped": []
        }
        # Store values from earlier tests for use in later tests
        self.context = {
            "invoice_no": None,
            "invoice_id": None,
            "reference_no": None,
            "application_id": None,
            "goods_id": None,
            "goods_code": None,
            "task_id": None,
            "business_key": None,
            "branch_id": None,
            "commodity_category_id": None,
            "excise_duty_code": None
        }
    
    def test_endpoint(self, code: str, name: str, test_func, skip: bool = False):
        """Run a single endpoint test and record results."""
        print_endpoint(code, name)
        if skip:
            print("⚠️  SKIPPED")
            self.results["skipped"].append(code)
            return True
        try:
            result = test_func()
            self.results["passed"].append(code)
            print(f"✅ PASSED")
            if result:
                print_response(result)
            return True
        except Exception as e:
            self.results["failed"].append(code)
            handle_error(code, e)
            return False
    
    # =========================================================================
    # AUTHENTICATION & INITIALIZATION TESTS
    # =========================================================================
    
    def test_t101_get_server_time(self):
        """T101: Get Server Time - Test API connectivity."""
        # Request: Null/Empty
        # Response: { "currentTime": "dd/MM/yyyy HH:mm:ss" }
        response = self.client.get_server_time()
        print(response)
        assert "currentTime" in response.get("data", {}).get("content", {}) or "currentTime" in response
        return response
    
    def test_t102_client_init(self):
        """T102: Client Initialization - Returns server public key."""
        # Request: { "otp": "100983" } (optional)
        # Response: { "clientPriKey": "...", "serverPubKey": "...", "keyTable": "..." }
        response = self.client.client_init()
        content = response.get("data", {}).get("content", response)
        assert "serverPubKey" in content or "clientPriKey" in content
        return response
    
    def test_t103_sign_in(self):
        """T103: Sign In - Login and retrieve taxpayer/device information."""
        # Request: Null
        # Response: Full taxpayer, device, branch, taxType info
        response = self.client.sign_in()
        content = response.get("data", {}).get("content", {})
        assert "taxpayer" in content or "device" in content
        # Store context for later tests
        if "taxpayer" in content:
            self.context["tin"] = content["taxpayer"].get("tin")
        return response
    
    def test_t104_get_symmetric_key(self):
        """T104: Get Symmetric Key - Fetch AES key for encryption."""
        # Request: Null
        # Response: { "passowrdDes": "...", "sign": "..." }
        response = self.client.get_symmetric_key()
        # Key is stored in key_client, response may be empty dict
        assert self.key_client._aes_key is not None or isinstance(response, dict)
        return response
    
    def test_t105_forget_password(self):
        """T105: Forget Password - Reset user password (test mode)."""
        # Request: { "userName": "admin", "changedPassword": "123456" }
        # Response: Null
        test_user = f"test_{int(time.time())}"
        response = self.client.forget_password(test_user, "TempPass123!")
        # May fail in test env, that's OK
        return response
    
    # =========================================================================
    # INVOICE OPERATIONS TESTS
    # =========================================================================
    
    def test_t106_query_all_invoices(self):
        """T106: Invoice/Receipt Query - All invoice types with pagination."""
        # Request: filters with pagination
        # Response: { "page": {...}, "records": [...] }
        today = get_date_timestamp()
        filters = {
            "startDate": today,
            "endDate": today,
            "pageNo": "1",
            "pageSize": "10",
            "invoiceType": "1",  # Invoice/Receipt
            "invoiceKind": "1"   # Invoice
        }
        response = self.client.query_all_invoices(filters)
        content = response.get("data", {}).get("content", response)
        assert "page" in content or "records" in content or isinstance(content, list)
        return response
    
    def test_t107_query_normal_invoices(self):
        """T107: Query Normal Invoice/Receipt - For credit/debit note eligibility."""
        # Request: filters for eligible invoices
        # Response: { "page": {...}, "records": [...] }
        today = get_date_timestamp()
        filters = {
            "startDate": today,
            "endDate": today,
            "pageNo": "1",
            "pageSize": "10",
            "invoiceType": "1"
        }
        response = self.client.query_invoices(filters)
        content = response.get("data", {}).get("content", response)
        # May return empty if no eligible invoices
        assert isinstance(content, (dict, list))
        return response
    
    def test_t108_invoice_details(self):
        """T108: Invoice Details - Get full invoice details by invoice number."""
        # Request: { "invoiceNo": "..." }
        # Response: Full invoice structure with sellerDetails, goodsDetails, etc.
        # Try with a known invoice or skip if none available
        if self.context.get("invoice_no"):
            response = self.client.verify_invoice(self.context["invoice_no"])
            content = response.get("data", {}).get("content", response)
            assert "basicInformation" in content or "sellerDetails" in content
            return response
        else:
            # Create minimal test - may fail, that's expected
            test_inv = f"TEST{int(time.time())}"
            response = self.client.verify_invoice(test_inv)
            return response
    
    def test_t130_upload_goods(self):
        """T130: Goods Upload - Add or modify goods/products."""
        # Request: List of goods with operationType, goodsCode, etc.
        # Response: List with returnCode/returnMessage per item
        goods_code = f"TEST_GOODS_{int(time.time())}"
        goods_data = [{
            "operationType": "101",  # 101=add, 102=modify
            "goodsName": "Test Product",
            "goodsCode": goods_code,
            "measureUnit": "101",  # per stick from T115
            "unitPrice": "1000.00",
            "currency": "101",  # UGX from T115
            "commodityCategoryId": "10111301",  # Standard category
            "haveExciseTax": "102",  # 101=Yes, 102=No
            "description": "Test product for integration",
            "stockPrewarning": "10",
            "havePieceUnit": "102",
            "haveOtherUnit": "102",
            "goodsTypeCode": "101",  # 101=Goods, 102=Fuel
            "haveCustomsUnit": "102"
        }]
        response = self.client.upload_goods(goods_data)
        content = response.get("data", {}).get("content", response)
        # Store for later use
        self.context["goods_code"] = goods_code
        return response
    
    def test_t109_upload_invoice(self):
        """T109: Billing Upload - Upload invoice/receipt/debit note."""
        # Request: Full invoice structure
        # Response: Invoice with assigned invoiceNo, antifakeCode, qrCode
        timestamp = get_timestamp()
        invoice_data = {
            "sellerDetails": {
                "tin": self.config.get("tin", ""),
                "ninBrn": self.config.get("brn", ""),
                "legalName": "Test Seller",
                "businessName": "Test Business",
                "address": "Test Address",
                "mobilePhone": "0772140000",
                "linePhone": "0414123456",
                "emailAddress": "test@example.com",
                "placeOfBusiness": "Kampala",
                "referenceNo": f"REF_{int(time.time())}",
                "isCheckReferenceNo": "0"
            },
            "basicInformation": {
                "deviceNo": self.config.get("device_no", ""),
                "issuedDate": timestamp,
                "operator": "test_operator",
                "currency": "UGX",
                "invoiceType": "1",  # 1=Invoice/Receipt
                "invoiceKind": "1",  # 1=Invoice, 2=Receipt
                "dataSource": "103",  # 103=WebService API
                "invoiceIndustryCode": "101"  # 101=General Industry
            },
            "buyerDetails": {
                "buyerTin": "1000029771",  # Test TIN
                "buyerNinBrn": "TEST001",
                "buyerLegalName": "Test Buyer",
                "buyerBusinessName": "Test Buyer Co",
                "buyerAddress": "Buyer Address",
                "buyerEmail": "buyer@example.com",
                "buyerMobilePhone": "0772999999",
                "buyerLinePhone": "0414999999",
                "buyerPlaceOfBusi": "Buyer Place",
                "buyerType": "0",  # 0=B2B, 1=B2C, 2=Foreigner, 3=B2G
                "buyerCitizenship": "UG-Uganda",
                "buyerSector": "Private",
                "buyerReferenceNo": "BUYER_REF_001"
            },
            "goodsDetails": [{
                "item": "Test Item",
                "itemCode": "TEST001",
                "qty": "1",
                "unitOfMeasure": "101",
                "unitPrice": "1000.00",
                "total": "1000.00",
                "taxRate": "0.18",
                "tax": "180.00",
                "orderNumber": "0",
                "discountFlag": "2",  # 2=non-discount
                "deemedFlag": "2",    # 2=not deemed
                "exciseFlag": "2",    # 2=not excise
                "goodsCategoryId": "100000000",
                "goodsCategoryName": "Standard",
                "vatApplicableFlag": "1"
            }],
            "taxDetails": [{
                "taxCategoryCode": "01",  # 01=Standard 18%
                "netAmount": "1000.00",
                "taxRate": "0.18",
                "taxAmount": "180.00",
                "grossAmount": "1180.00",
                "taxRateName": "Standard"
            }],
            "summary": {
                "netAmount": "1000.00",
                "taxAmount": "180.00",
                "grossAmount": "1180.00",
                "itemCount": "1",
                "modeCode": "1",  # 1=Online, 0=Offline
                "remarks": "Test invoice from integration test",
                "qrCode": ""  # Generated by server for offline mode
            },
            "payWay": [{
                "paymentMode": "102",  # 102=Cash
                "paymentAmount": "1180.00",
                "orderNumber": "a"
            }]
        }
        response = self.client.fiscalise_invoice(invoice_data)
        content = response.get("data", {}).get("content", response)
        # Store invoice number for later tests
        if "basicInformation" in content and "invoiceNo" in content["basicInformation"]:
            self.context["invoice_no"] = content["basicInformation"]["invoiceNo"]
            self.context["invoice_id"] = content["basicInformation"].get("invoiceId")
        return response
    
    def test_t129_batch_upload(self):
        """T129: Batch Invoice Upload - Upload multiple invoices."""
        # Request: List of { "invoiceContent": base64_encoded_json, "invoiceSignature": "..." }
        # Response: List of { "invoiceReturnCode": "...", "invoiceReturnMessage": "..." }
        # This is complex - in test mode, we'll test with empty/minimal batch
        batch_data = []
        response = self.client.fiscalise_batch_invoices(batch_data)
        # May return empty list or error - both acceptable in test
        return response
    
    # =========================================================================
    # CREDIT/DEBIT NOTE OPERATIONS TESTS
    # =========================================================================
    
    def test_t110_credit_note_application(self):
        """T110: Credit Application - Apply for credit note."""
        # Request: Credit note application with original invoice reference
        # Response: { "referenceNo": "..." }
        if not self.context.get("invoice_no"):
            print("⚠️  No invoice available for credit note test")
            return None
        
        application_data = {
            "oriInvoiceId": self.context.get("invoice_id", ""),
            "oriInvoiceNo": self.context["invoice_no"],
            "reasonCode": "102",  # Cancellation of purchase
            "reason": "Test credit note application",
            "applicationTime": get_timestamp(),
            "invoiceApplyCategoryCode": "101",  # 101=creditNote
            "currency": "UGX",
            "contactName": "Test Contact",
            "contactMobileNum": "0772140000",
            "contactEmail": "contact@example.com",
            "source": "103",  # WebService API
            "remarks": "Integration test credit note",
            "sellersReferenceNo": f"CRED_REF_{int(time.time())}",
            "goodsDetails": [{
                "item": "Test Item",
                "itemCode": "TEST001",
                "qty": "-1",  # Negative for credit
                "unitOfMeasure": "101",
                "unitPrice": "1000.00",
                "total": "-1000.00",
                "taxRate": "0.18",
                "tax": "-180.00",
                "orderNumber": "0",
                "deemedFlag": "2",
                "exciseFlag": "2",
                "goodsCategoryId": "100000000",
                "vatApplicableFlag": "1"
            }],
            "taxDetails": [{
                "taxCategoryCode": "01",
                "netAmount": "-1000.00",
                "taxRate": "0.18",
                "taxAmount": "-180.00",
                "grossAmount": "-1180.00",
                "taxRateName": "Standard"
            }],
            "summary": {
                "netAmount": "-1000.00",
                "taxAmount": "-180.00",
                "grossAmount": "-1180.00",
                "itemCount": "1",
                "modeCode": "1",
                "qrCode": ""
            },
            "basicInformation": {
                "operator": "test_operator",
                "invoiceKind": "1",
                "invoiceIndustryCode": "101"
            }
        }
        response = self.client.apply_credit_note(application_data)
        content = response.get("data", {}).get("content", response)
        if "referenceNo" in content:
            self.context["reference_no"] = content["referenceNo"]
        return response
    
    def test_t111_query_credit_note_status(self):
        """T111: Credit/Debit Note Application List Query."""
        # Request: Filters for application queries
        # Response: { "page": {...}, "records": [...] }
        filters = {
            "startDate": get_date_timestamp(),
            "endDate": get_date_timestamp(),
            "pageNo": "1",
            "pageSize": "10",
            "invoiceApplyCategoryCode": "101",  # credit note
            "queryType": "1"  # Current user's applications
        }
        if self.context.get("reference_no"):
            filters["referenceNo"] = self.context["reference_no"]
        
        response = self.client.query_credit_note_status(filters)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, (dict, list))
        return response
    
    def test_t112_credit_application_detail(self):
        """T112: Credit Note Application Details."""
        # Request: { "id": "application_id" }
        # Response: Full application details
        if self.context.get("application_id"):
            response = self.client.get_credit_application_detail(self.context["application_id"])
            content = response.get("data", {}).get("content", response)
            assert "goodsDetails" in content or "summary" in content
            return response
        else:
            # Try with reference_no lookup first to get id
            return None
    
    def test_t113_approve_credit_note(self):
        """T113: Credit Note Approval - Approve or reject application."""
        # Request: { "referenceNo": "...", "approveStatus": "101|103", "taskId": "...", "remark": "..." }
        # Response: Null
        if self.context.get("reference_no") and self.context.get("task_id"):
            response = self.client.approve_credit_note(
                reference_no=self.context["reference_no"],
                approve=True,  # 101=Approved, 103=Rejected
                task_id=self.context["task_id"],
                remark="Approved via integration test"
            )
            return response
        else:
            print("⚠️  Missing reference_no or task_id for approval test")
            return None
    
    def test_t114_cancel_credit_note_application(self):
        """T114: Cancel Credit/Debit Note Application."""
        # Request: { "oriInvoiceId": "...", "invoiceNo": "...", "reasonCode": "...", ... }
        # Response: Null
        if self.context.get("invoice_no"):
            response = self.client.cancel_credit_note_application(
                ori_invoice_id=self.context.get("invoice_id", ""),
                invoice_no=self.context["invoice_no"],
                reason_code="103",  # Other reasons
                reason="Test cancellation",
                cancel_type="104"  # 104=cancel of Credit Note
            )
            return response
        return None
    
    def test_t118_query_credit_application_details(self):
        """T118: Query Credit Note and Cancel Debit Note Application Details."""
        # Request: { "id": "application_id" }
        # Response: Application details with goods/tax/summary
        if self.context.get("application_id"):
            response = self.client._send(
                "query_credit_application_details",
                {"id": self.context["application_id"]},
                encrypt=True, decrypt=True
            )
            return response
        return None
    
    def test_t120_void_application(self):
        """T120: Void Credit/Debit Note Application."""
        # Request: { "businessKey": "...", "referenceNo": "..." }
        # Response: Null
        if self.context.get("business_key") and self.context.get("reference_no"):
            response = self.client.void_credit_debit_application(
                business_key=self.context["business_key"],
                reference_no=self.context["reference_no"]
            )
            return response
        return None
    
    def test_t122_query_invalid_credit(self):
        """T122: Query Cancel Credit Note Details."""
        # Request: { "invoiceNo": "..." }
        # Response: Cancel credit note details
        if self.context.get("invoice_no"):
            response = self.client.query_invalid_credit_note(self.context["invoice_no"])
            return response
        return None
    
    # =========================================================================
    # TAXPAYER & BRANCH OPERATIONS TESTS
    # =========================================================================
    
    def test_t119_query_taxpayer(self):
        """T119: Query Taxpayer Information By TIN."""
        # Request: { "tin": "...", "ninBrn": "..." } (one required)
        # Response: { "taxpayer": { ... } }
        response = self.client.query_taxpayer_by_tin(
            tin=self.config.get("tin", "1000029771")
        )
        content = response.get("data", {}).get("content", response)
        assert "taxpayer" in content
        return response
    
    def test_t137_check_taxpayer_type(self):
        """T137: Check Exempt/Deemed Taxpayer."""
        # Request: { "tin": "...", "commodityCategoryCode": "..." }
        # Response: { "taxpayerType": "...", "deemedAndExemptProjectList": [...] }
        response = self.client.check_taxpayer_type(
            tin=self.config.get("tin", ""),
            commodity_category_code="100000000"
        )
        content = response.get("data", {}).get("content", response)
        assert "taxpayerType" in content or "deemedAndExemptProjectList" in content
        return response
    
    def test_t138_get_branches(self):
        """T138: Get All Branches."""
        # Request: Null or { "tin": "..." }
        # Response: List of { "branchId": "...", "branchName": "..." }
        response = self.client.get_registered_branches()
        content = response.get("data", {}).get("content", response)
        # Store first branch for later tests
        if isinstance(content, list) and len(content) > 0:
            self.context["branch_id"] = content[0].get("branchId")
        assert isinstance(content, list)
        return response
    
    # =========================================================================
    # COMMODITY & EXCISE OPERATIONS TESTS
    # =========================================================================
    
    def test_t115_system_dictionary(self):
        """T115: System Dictionary Update - Get tax rates, currencies, etc."""
        # Request: Null
        # Response: Dictionary with currencyType, rateUnit, payWay, etc.
        response = self.client.update_system_dictionary()
        content = response.get("data", {}).get("content", response)
        assert "currencyType" in content or "rateUnit" in content or "payWay" in content
        # Store category info for later
        if "sector" in content and isinstance(content["sector"], list):
            for cat in content["sector"]:
                if cat.get("parentClass") == "0":
                    self.context["commodity_category_id"] = cat.get("code")
                    break
        return response
    
    def test_t123_query_commodity_categories(self):
        """T123: Query All Commodity Categories."""
        # Request: Null
        # Response: List of category objects
        response = self.client.query_commodity_categories_all()
        content = response if isinstance(response, list) else response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t124_query_commodity_categories_page(self):
        """T124: Query Commodity Category Pagination."""
        # Request: { "pageNo": "1", "pageSize": "10" }
        # Response: { "page": {...}, "records": [...] }
        response = self.client.query_commodity_categories(page_no=1, page_size=10)
        content = response.get("data", {}).get("content", response)
        assert "page" in content or "records" in content
        return response
    
    def test_t125_query_excise_duty(self):
        """T125: Query Excise Duty Codes."""
        # Request: Null
        # Response: { "exciseDutyList": [...] }
        response = self.client.query_excise_duty_codes()
        content = response if isinstance(response, dict) else response.get("data", {}).get("content", response)
        assert "exciseDutyList" in content or isinstance(content, dict)
        # Store first excise code for later
        if "exciseDutyList" in content and content["exciseDutyList"]:
            self.context["excise_duty_code"] = content["exciseDutyList"][0].get("exciseDutyCode")
        return response
    
    def test_t134_commodity_incremental(self):
        """T134: Commodity Category Incremental Update."""
        # Request: { "commodityCategoryVersion": "..." }
        # Response: List of changed categories
        response = self.client.sync_commodity_categories(local_version="1.0")
        content = response.get("data", {}).get("content", response)
        # May return empty if no changes
        assert isinstance(content, (list, dict))
        return response
    
    def test_t146_query_commodity_by_date(self):
        """T146: Query Commodity/Excise Duty by Issue Date."""
        # Request: { "categoryCode": "...", "type": "1|2", "issueDate": "..." }
        # Response: { "commodityCategory": {...} } or { "exciseDuty": {...} }
        response = self.client.query_commodity_by_date(
            category_code="13101501",
            item_type="1",  # 1=Commodity Category, 2=Excise Duty
            issue_date=get_timestamp()
        )
        content = response.get("data", {}).get("content", response)
        assert "commodityCategory" in content or "exciseDuty" in content or isinstance(content, dict)
        return response
    
    def test_t185_query_hs_codes(self):
        """T185: Query HS Code List."""
        # Request: Null
        # Response: List of HS code objects
        response = self.client.query_hs_codes()
        content = response if isinstance(response, list) else response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    # =========================================================================
    # EXCHANGE RATE OPERATIONS TESTS
    # =========================================================================
    
    def test_t121_get_exchange_rate(self):
        """T121: Acquire Exchange Rate for Single Currency."""
        # Request: { "currency": "USD", "issueDate": "..." }
        # Response: { "currency": "USD", "rate": "...", ... }
        response = self.client.get_exchange_rate(currency="USD", issue_date=get_date_timestamp())
        content = response.get("data", {}).get("content", response)
        assert "currency" in content and "rate" in content
        return response
    
    def test_t126_get_all_exchange_rates(self):
        """T126: Get All Exchange Rates."""
        # Request: { "issueDate": "..." } (optional)
        # Response: List of { "currency": "...", "rate": "...", ... }
        response = self.client.get_all_exchange_rates(issue_date=get_date_timestamp())
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, list) and len(content) > 0
        return response
    
    # =========================================================================
    # GOODS & STOCK OPERATIONS TESTS
    # =========================================================================
    
    def test_t127_inquire_goods(self):
        """T127: Goods/Services Inquiry with pagination."""
        # Request: Filters for goods query
        # Response: { "page": {...}, "records": [...] }
        filters = {
            "pageNo": "1",
            "pageSize": "10"
        }
        if self.context.get("goods_code"):
            filters["goodsCode"] = self.context["goods_code"]
        
        response = self.client.inquire_goods(filters)
        content = response.get("data", {}).get("content", response)
        assert "page" in content or "records" in content
        # Store goods id if available
        if "records" in content and isinstance(content["records"], list) and content["records"]:
            self.context["goods_id"] = content["records"][0].get("id")
        return response
    
    def test_t144_query_goods_by_code(self):
        """T144: Query Goods by Code."""
        # Request: { "goodsCode": "0001,0002", "tin": "..." }
        # Response: List of goods objects
        if self.context.get("goods_code"):
            response = self.client.query_goods_by_code(
                goods_code=self.context["goods_code"],
                tin=self.config.get("tin")
            )
            content = response.get("data", {}).get("content", response)
            assert isinstance(content, list)
            return response
        return None
    
    def test_t128_query_stock(self):
        """T128: Query Stock Quantity by Goods ID."""
        # Request: { "id": "goods_id", "branchId": "..." }
        # Response: { "stock": "...", "stockPrewarning": "..." }
        print('self.context.get("goods_id"):', self.context.get("goods_id"))
        if self.context.get("goods_id"):
            response = self.client.query_stock_quantity(
                goods_id=self.context["goods_id"],
                branch_id=self.context.get("branch_id")
            )
            content = response.get("data", {}).get("content", response)
            assert "stock" in content
            return response
        return None
    
    def test_t131_maintain_stock(self):
        """T131: Goods Stock Maintain - Stock in/out operations."""
        # Request: { "goodsStockIn": {...}, "goodsStockInItem": [...] }
        # Response: List with returnCode per item
        if not self.context.get("goods_id") and not self.context.get("goods_code"):
            print("⚠️  No goods available for stock maintain test")
            return None
        
        stock_data = {
            "goodsStockIn": {
                "operationType": "101",  # 101=Increase, 102=Decrease
                "supplierTin": self.config.get("tin", ""),
                "supplierName": "Test Supplier",
                "remarks": "Integration test stock in",
                "stockInDate": get_date_timestamp(),
                "stockInType": "102",  # 102=Local Purchase
                # "branchId": self.context.get("branch_id", ""),
                "isCheckBatchNo": "0",
                "rollBackIfError": "0",
                "goodsTypeCode": "101"
            },
            "goodsStockInItem": [{
                "commodityGoodsId": self.context.get("goods_id", ""),
                "goodsCode": self.context.get("goods_code", ""),
                "measureUnit": "101",
                "quantity": "10",
                "unitPrice": "100.00",
                "remarks": "Test stock entry"
            }]
        }
        response = self.client.maintain_stock(stock_data)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t139_transfer_stock(self):
        """T139: Goods Stock Transfer Between Branches."""
        # Request: { "goodsStockTransfer": {...}, "goodsStockTransferItem": [...] }
        # Response: List with returnCode per item
        if not self.context.get("branch_id"):
            print("⚠️  No branch available for stock transfer test")
            return None
        
        transfer_data = {
            "goodsStockTransfer": {
                "sourceBranchId": self.context["branch_id"],
                "destinationBranchId": self.context["branch_id"],  # Same for test
                "transferTypeCode": "101",  # 101=Out of Stock Adjust
                "remarks": "Test transfer",
                "rollBackIfError": "0",
                "goodsTypeCode": "101"
            },
            "goodsStockTransferItem": [{
                "commodityGoodsId": self.context.get("goods_id", ""),
                "goodsCode": self.context.get("goods_code", ""),
                "measureUnit": "101",
                "quantity": "5",
                "remarks": "Test transfer item"
            }]
        }
        response = self.client.transfer_stock(transfer_data)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t145_stock_records_query(self):
        """T145: Goods Stock Records Query."""
        # Request: Filters for stock records
        # Response: { "page": {...}, "records": [...] }
        filters = {
            "pageNo": "1",
            "pageSize": "10",
            "startDate": get_date_timestamp(),
            "endDate": get_date_timestamp()
        }
        response = self.client.query_stock_records(filters)
        content = response.get("data", {}).get("content", response)
        assert "page" in content or "records" in content
        return response
    
    def test_t147_stock_records_query_alt(self):
        """T147: Goods Stock Records Query (Current Branch Only)."""
        # Request: Filters with branch context
        # Response: { "page": {...}, "records": [...] }
        filters = {
            "pageNo": "1",
            "pageSize": "10",
            "startDate": get_date_timestamp(),
            "endDate": get_date_timestamp(),
            "stockInType": "101"
        }
        response = self.client.query_stock_records_alt(filters)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, dict)
        return response
    
    def test_t148_stock_records_detail(self):
        """T148: Goods Stock Record Detail Query."""
        # Request: { "id": "record_id" }
        # Response: Full stock record with goods details
        # Would need a valid record ID from T145/T147
        return None  # Skip - requires prior record ID
    
    def test_t149_stock_adjust_records(self):
        """T149: Goods Stock Adjust Records Query."""
        # Request: Filters for adjust records
        # Response: { "page": {...}, "records": [...] }
        filters = {
            "pageNo": "1",
            "pageSize": "10",
            "startDate": get_date_timestamp(),
            "endDate": get_date_timestamp()
        }
        response = self.client.query_stock_adjust_records(filters)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, dict)
        return response
    
    def test_t160_stock_adjust_detail(self):
        """T160: Goods Stock Adjust Detail Query."""
        # Request: { "id": "adjust_id" }
        # Response: Full adjust record details
        return None  # Skip - requires prior adjust ID
    
    def test_t183_stock_transfer_records(self):
        """T183: Goods Stock Transfer Records Query."""
        # Request: Filters for transfer records
        # Response: { "page": {...}, "records": [...] }
        filters = {
            "pageNo": "1",
            "pageSize": "10",
            "startDate": get_date_timestamp(),
            "endDate": get_date_timestamp()
        }
        response = self.client.query_stock_transfer_records(filters)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, dict)
        return response
    
    def test_t184_stock_transfer_detail(self):
        """T184: Goods Stock Transfer Detail Query."""
        # Request: { "id": "transfer_id" }
        # Response: Full transfer record details
        return None  # Skip - requires prior transfer ID
    
    def test_t177_negative_stock_config(self):
        """T177: Negative Stock Configuration Inquiry."""
        # Request: Null
        # Response: { "goodsStockLimit": {...}, "goodsStockLimitCategoryList": [...] }
        response = self.client.query_negative_stock_config()
        content = response if isinstance(response, dict) else response.get("data", {}).get("content", response)
        assert "goodsStockLimit" in content or isinstance(content, dict)
        return response
    
    # =========================================================================
    # EDC / FUEL SPECIFIC OPERATIONS TESTS
    # =========================================================================
    
    def test_t162_query_fuel_type(self):
        """T162: Query Fuel Type."""
        # Request: Null
        # Response: List of fuel type objects
        response = self.client.query_fuel_type()
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t163_upload_shift_info(self):
        """T163: Upload Shift Information."""
        # Request: Shift data with volumes, fuel type, etc.
        # Response: Null
        shift_data = {
            "shiftNo": f"SHIFT_{int(time.time())}",
            "startVolume": "1000.00",
            "endVolume": "1000.00",
            "fuelType": "Petrol",
            "goodsId": "12345",
            "goodsCode": "PETROL_001",
            "invoiceAmount": "5000.00",
            "invoiceNumber": "10",
            "nozzleNo": "NOZZLE_001",
            "pumpNo": "PUMP_001",
            "tankNo": "TANK_001",
            "userName": "test_user",
            "userCode": "TEST001",
            "startTime": get_timestamp(),
            "endTime": get_timestamp()
        }
        response = self.client.upload_shift_info(shift_data)
        return response
    
    def test_t164_upload_edc_disconnect(self):
        """T164: Upload EDC Disconnection Data."""
        # Request: List of disconnect logs
        # Response: Null
        logs = [{
            "deviceNumber": self.config.get("device_no", "TEST_DEVICE"),
            "disconnectedType": "101",  # 101=TCS disconnected
            "disconnectedTime": get_timestamp(),
            "remarks": "Test disconnect log"
        }]
        response = self.client.upload_edc_disconnect(logs)
        return response
    
    def test_t166_update_buyer_details(self):
        """T166: Update Buyer Details on EDC Invoice."""
        # Request: Buyer details update for specific invoice
        # Response: Null
        if self.context.get("invoice_no"):
            update_data = {
                "invoiceNo": self.context["invoice_no"],
                "buyerTin": "1000029771",
                "buyerLegalName": "Updated Buyer Name",
                "buyerBusinessName": "Updated Business",
                "buyerAddress": "Updated Address",
                "buyerEmailAddress": "updated@example.com",
                "buyerMobilePhone": "0772999999",
                "buyerType": "0",
                "createDateStr": get_timestamp()
            }
            response = self.client.update_buyer_details(update_data)
            return response
        return None
    
    def test_t167_edc_invoice_query(self):
        """T167: EDC Invoice/Receipt Inquiry."""
        # Request: Filters for EDC invoices
        # Response: { "page": {...}, "records": [...] }
        filters = {
            "fuelType": "Petrol",
            "startDate": get_date_timestamp(),
            "endDate": get_date_timestamp(),
            "pageNo": "1",
            "pageSize": "10",
            "queryType": "1",
            "branchId": self.context.get("branch_id", "")
        }
        response = self.client.edc_invoice_query(filters)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, dict)
        return response
    
    def test_t168_query_fuel_pump_version(self):
        """T168: Query Fuel Pump Version."""
        # Request: Null
        # Response: { "fuelPumpList": [...], "fuelDefaultBuyerList": [...] }
        response = self.client.query_fuel_pump_version()
        content = response.get("data", {}).get("content", response)
        assert "fuelPumpList" in content or "fuelDefaultBuyerList" in content
        return response
    
    def test_t169_query_pump_nozzle_tank(self):
        """T169: Query Pump/Nozzle/Tank by Pump Number."""
        # Request: { "id": "pump_id" }
        # Response: { "fuelPump": {...}, "fuelNozzleList": [...], "fuelTankList": [...] }
        # Would need valid pump ID from T168
        return None  # Skip - requires prior pump ID
    
    def test_t170_query_edc_location(self):
        """T170: Query EFD Location History."""
        # Request: { "deviceNumber": "...", "startDate": "...", "endDate": "..." }
        # Response: List of location records
        response = self.client.query_edc_location(
            device_number=self.config.get("device_no", ""),
            start_date=get_date_timestamp(),
            end_date=get_date_timestamp()
        )
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t171_query_edc_uom_rate(self):
        """T171: Query EDC UoM Exchange Rate."""
        # Request: Null
        # Response: List of { "unitOfMeasure": "...", "exchangeRate": "..." }
        response = self.client.query_edc_uom_rate()
        content = response if isinstance(response, list) else response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t172_upload_nozzle_status(self):
        """T172: Fuel Nozzle Status Upload."""
        # Request: { "nozzleId": "...", "nozzleNo": "...", "status": "..." }
        # Response: Null
        response = self.client.upload_nozzle_status(
            nozzle_id="TEST_NOZZLE_ID",
            nozzle_no="NOZZLE_TEST_001",
            status="1"  # 1=Available
        )
        return response
    
    def test_t173_query_edc_device_version(self):
        """T173: Query EDC Device Version."""
        # Request: Null
        # Response: List of device version objects
        response = self.client.query_edc_device_version()
        content = response if isinstance(response, list) else response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t176_upload_device_status(self):
        """T176: Upload Device Issuing Status."""
        # Request: { "deviceNo": "...", "deviceIssuingStatus": "..." }
        # Response: Null
        response = self.client.upload_device_status(
            device_no=self.config.get("device_no", ""),
            status="101"  # 101=Ready
        )
        return response
    
    # =========================================================================
    # AGENT / USSD / FREQUENT CONTACTS TESTS
    # =========================================================================
    
    def test_t175_ussd_account_create(self):
        """T175: Account Creation for USSD Taxpayer."""
        # Request: { "tin": "...", "mobileNumber": "..." }
        # Response: Null
        response = self.client.ussd_account_create(
            tin=self.config.get("tin", ""),
            mobile_number="0772140000"
        )
        return response
    
    def test_t178_efd_transfer(self):
        """T178: EFD Transfer to Another Branch."""
        # Request: { "destinationBranchId": "...", "remarks": "..." }
        # Response: Null
        if self.context.get("branch_id"):
            response = self.client.efd_transfer(
                destination_branch_id=self.context["branch_id"],
                remarks="Test EFD transfer"
            )
            return response
        return None
    
    def test_t179_query_agent_relation(self):
        """T179: Query Agent Relation Information."""
        # Request: { "tin": "..." }
        # Response: { "agentTaxpayerList": [...] }
        response = self.client.query_agent_relation(
            tin="1010039929"
        )
        content = response.get("data", {}).get("content", response)
        assert "agentTaxpayerList" in content or isinstance(content, dict)
        return response
    
    def test_t180_query_principal_agent(self):
        """T180: Query Principal Agent TIN Information."""
        # Request: { "tin": "...", "branchId": "..." }
        # Response: Agent configuration info
        response = self.client.query_principal_agent(
            tin="1009837013",
            branch_id="210059212594887180"
        )
        content = response.get("data", {}).get("content", response)
        assert "issueTaxTypeRestrictions" in content or "taxType" in content
        return response
    
    def test_t181_upload_frequent_contacts(self):
        """T181: Upload Frequent Contacts."""
        # Request: Contact data with operationType
        # Response: Null
        contact_data = {
            "operationType": "101",  # 101=Add, 102=Modify, 103=Delete
            "buyerType": "0",  # 0=B2B
            "buyerTin": "1000029771",
            "buyerNinBrn": "TEST_BRN",
            "buyerLegalName": "Frequent Buyer",
            "buyerBusinessName": "Frequent Buyer Co",
            "buyerEmail": "frequent@example.com",
            "buyerLinePhone": "0414123456",
            "buyerAddress": "Buyer Address",
            "buyerCitizenship": "UG-Uganda"
        }
        response = self.client.upload_frequent_contacts(contact_data)
        return response
    
    def test_t182_get_frequent_contacts(self):
        """T182: Get Frequent Contacts."""
        # Request: Optional filters
        # Response: List of contact objects
        response = self.client.get_frequent_contacts(
            buyer_tin="1000029771",
            buyer_legal_name="Frequent Buyer"
        )
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    # =========================================================================
    # EXPORT / CUSTOMS OPERATIONS TESTS
    # =========================================================================
    
    def test_t187_query_fdn_status(self):
        """T187: Query Export FDN Status."""
        # Request: { "invoiceNo": "..." }
        # Response: { "invoiceNo": "...", "documentStatusCode": "..." }
        if self.context.get("invoice_no"):
            response = self.client.query_fdn_status(self.context["invoice_no"])
            content = response.get("data", {}).get("content", response)
            assert "invoiceNo" in content
            return response
        return None
    
    # =========================================================================
    # REPORTING & LOGGING TESTS
    # =========================================================================
    
    def test_t116_z_report_upload(self):
        """T116: Z-Report Daily Upload."""
        # Request: Z-report data (structure TBD per docs)
        # Response: Null
        # Minimal test payload
        report_data = {
            "deviceNo": self.config.get("device_no", ""),
            "reportDate": get_date_timestamp(),
            "totalSales": "0.00",
            "totalTax": "0.00"
        }
        response = self.client.upload_z_report(report_data)
        return response
    
    def test_t117_invoice_checks(self):
        """T117: Invoice Checks - Batch verify multiple invoices."""
        # Request: List of { "invoiceNo": "...", "invoiceType": "..." }
        # Response: List of verified invoices
        checks = []
        if self.context.get("invoice_no"):
            checks.append({
                "invoiceNo": self.context["invoice_no"],
                "invoiceType": "1"  # 1=Invoice/Receipt
            })
        response = self.client.verify_invoices_batch(checks)
        content = response.get("data", {}).get("content", response)
        assert isinstance(content, list)
        return response
    
    def test_t132_upload_exception_logs(self):
        """T132: Upload Exception Logs."""
        # Request: List of exception log entries
        # Response: Null
        logs = [{
            "interruptionTypeCode": "101",  # 101=Disconnected
            "description": "Test exception log",
            "errorDetail": "Integration test error detail",
            "interruptionTime": get_timestamp()
        }]
        response = self.client.upload_exception_logs(logs)
        return response
    
    def test_t133_tcs_upgrade_download(self):
        """T133: TCS Upgrade System File Download."""
        # Request: { "tcsVersion": "...", "osType": "..." }
        # Response: File download info with commands and SQL
        response = self.client.tcs_upgrade_download(
            tcs_version="1",
            os_type="1"  # 0=linux, 1=windows
        )
        content = response.get("data", {}).get("content", response)
        assert "tcsversion" in content or "fileList" in content or isinstance(content, dict)
        return response
    
    def test_t135_get_tcs_latest_version(self):
        """T135: Get TCS Latest Version."""
        # Request: Null
        # Response: { "latesttcsversion": "..." }
        response = self.client.get_tcs_latest_version()
        content = response.get("data", {}).get("content", response)
        assert "latesttcsversion" in content
        return response
    
    def test_t136_certificate_upload(self):
        """T136: Certificate Public Key Upload."""
        # Request: { "fileName": "...", "verifyString": "...", "fileContent": "..." }
        # Response: Null
        # Test with minimal valid-looking data
        test_cert = "MIIDFjCCAf6gAwIBAgIRAKPGAol9CEdpkIoFa8huM6zfj1WEBRxteoo6PH46un4FGj4N6ioIGzVr9G40uhQGdm16ZU+q44XjW2oUnI9w="
        response = self.client.certificate_upload(
            file_name="test_cert.cer",
            verify_string=hashlib.md5(self.config.get("tin", "").encode()).hexdigest()[:30],
            file_content=test_cert
        )
        return response
    
    # =========================================================================
    # ADDITIONAL ENDPOINT TESTS (T186)
    # =========================================================================
    
    def test_t186_invoice_remain_details(self):
        """T186: Invoice Remain Details - Get invoice with remaining quantities."""
        # Request: { "invoiceNo": "..." }
        # Response: Invoice details with remainQty, remainAmount fields
        if self.context.get("invoice_no"):
            response = self.client.invoice_remain_details(self.context["invoice_no"])
            content = response.get("data", {}).get("content", response)
            # May have remainQty/remainAmount in goodsDetails
            assert "basicInformation" in content or "goodsDetails" in content
            return response
        return None
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Execute all endpoint tests in logical order."""
        print_section("EFRIS API COMPLETE ENDPOINT TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {self.client.config.get('env', 'unknown')}")
        print(f"TIN: {self.client.config.get('tin', 'unknown')}")
        print(f"Device: {self.client.config.get('device_no', 'unknown')}")
        
        # Authentication & Initialization (must run first)
        print_section("AUTHENTICATION & INITIALIZATION")
        self.test_endpoint("T101", "Get Server Time", self.test_t101_get_server_time)
        self.test_endpoint("T102", "Client Initialization", self.test_t102_client_init)
        self.test_endpoint("T103", "Sign In", self.test_t103_sign_in)
        self.test_endpoint("T104", "Get Symmetric Key", self.test_t104_get_symmetric_key)
        self.test_endpoint("T105", "Forget Password", self.test_t105_forget_password, skip=True)
        
        # System Dictionary (needed for other tests)
        print_section("SYSTEM DICTIONARY & REFERENCE DATA")
        self.test_endpoint("T115", "System Dictionary", self.test_t115_system_dictionary)
        self.test_endpoint("T123", "Query Commodity Categories", self.test_t123_query_commodity_categories)
        self.test_endpoint("T124", "Query Categories (Paginated)", self.test_t124_query_commodity_categories_page)
        self.test_endpoint("T125", "Query Excise Duty", self.test_t125_query_excise_duty)
        self.test_endpoint("T134", "Commodity Incremental Update", self.test_t134_commodity_incremental)
        self.test_endpoint("T146", "Query Commodity by Date", self.test_t146_query_commodity_by_date)
        self.test_endpoint("T185", "Query HS Codes", self.test_t185_query_hs_codes)
        
        # Exchange Rates
        print_section("EXCHANGE RATE OPERATIONS")
        self.test_endpoint("T121", "Get Exchange Rate", self.test_t121_get_exchange_rate)
        self.test_endpoint("T126", "Get All Exchange Rates", self.test_t126_get_all_exchange_rates)
        
        # Taxpayer & Branch Info
        print_section("TAXPAYER & BRANCH OPERATIONS")
        self.test_endpoint("T119", "Query Taxpayer by TIN", self.test_t119_query_taxpayer)
        self.test_endpoint("T137", "Check Taxpayer Type", self.test_t137_check_taxpayer_type)
        self.test_endpoint("T138", "Get Registered Branches", self.test_t138_get_branches)
        self.test_endpoint("T180", "Query Principal Agent", self.test_t180_query_principal_agent)
        self.test_endpoint("T179", "Query Agent Relation", self.test_t179_query_agent_relation)
        
        # Goods & Stock Operations
        print_section("GOODS & STOCK OPERATIONS")
        self.test_endpoint("T130", "Upload Goods", self.test_t130_upload_goods)
        self.test_endpoint("T127", "Inquire Goods", self.test_t127_inquire_goods)
        self.test_endpoint("T144", "Query Goods by Code", self.test_t144_query_goods_by_code)
        self.test_endpoint("T128", "Query Stock Quantity", self.test_t128_query_stock)
        self.test_endpoint("T131", "Maintain Stock", self.test_t131_maintain_stock)
        self.test_endpoint("T139", "Transfer Stock", self.test_t139_transfer_stock)
        self.test_endpoint("T145", "Stock Records Query", self.test_t145_stock_records_query)
        self.test_endpoint("T147", "Stock Records Query (Alt)", self.test_t147_stock_records_query_alt)
        self.test_endpoint("T149", "Stock Adjust Records", self.test_t149_stock_adjust_records)
        self.test_endpoint("T183", "Stock Transfer Records", self.test_t183_stock_transfer_records)
        self.test_endpoint("T177", "Negative Stock Config", self.test_t177_negative_stock_config)
        # Skip detail queries that need IDs from previous queries
        
        # Invoice Operations (core functionality)
        print_section("INVOICE OPERATIONS")
        self.test_endpoint("T106", "Query All Invoices", self.test_t106_query_all_invoices)
        self.test_endpoint("T107", "Query Normal Invoices", self.test_t107_query_normal_invoices)
        self.test_endpoint("T109", "Upload Invoice", self.test_t109_upload_invoice)
        self.test_endpoint("T108", "Invoice Details", self.test_t108_invoice_details)
        self.test_endpoint("T186", "Invoice Remain Details", self.test_t186_invoice_remain_details)
        self.test_endpoint("T129", "Batch Invoice Upload", self.test_t129_batch_upload, skip=True)
        self.test_endpoint("T117", "Invoice Checks", self.test_t117_invoice_checks)
        
        # Credit/Debit Note Operations
        print_section("CREDIT/DEBIT NOTE OPERATIONS")
        self.test_endpoint("T110", "Credit Note Application", self.test_t110_credit_note_application)
        self.test_endpoint("T111", "Query Credit Note Status", self.test_t111_query_credit_note_status)
        self.test_endpoint("T112", "Credit Application Detail", self.test_t112_credit_application_detail, skip=True)
        self.test_endpoint("T113", "Approve Credit Note", self.test_t113_approve_credit_note, skip=True)
        self.test_endpoint("T114", "Cancel Credit Note", self.test_t114_cancel_credit_note_application)
        self.test_endpoint("T118", "Query Application Details", self.test_t118_query_credit_application_details, skip=True)
        self.test_endpoint("T120", "Void Application", self.test_t120_void_application, skip=True)
        self.test_endpoint("T122", "Query Invalid Credit", self.test_t122_query_invalid_credit)
        
        # EDC / Fuel Operations
        print_section("EDC / FUEL SPECIFIC OPERATIONS")
        self.test_endpoint("T162", "Query Fuel Type", self.test_t162_query_fuel_type)
        self.test_endpoint("T163", "Upload Shift Info", self.test_t163_upload_shift_info)
        self.test_endpoint("T164", "Upload EDC Disconnect", self.test_t164_upload_edc_disconnect)
        self.test_endpoint("T167", "EDC Invoice Query", self.test_t167_edc_invoice_query)
        self.test_endpoint("T168", "Query Fuel Pump Version", self.test_t168_query_fuel_pump_version)
        self.test_endpoint("T170", "Query EFD Location", self.test_t170_query_edc_location)
        self.test_endpoint("T171", "Query EDC UoM Rate", self.test_t171_query_edc_uom_rate)
        self.test_endpoint("T172", "Upload Nozzle Status", self.test_t172_upload_nozzle_status)
        self.test_endpoint("T173", "Query EDC Device Version", self.test_t173_query_edc_device_version)
        self.test_endpoint("T176", "Upload Device Status", self.test_t176_upload_device_status)
        self.test_endpoint("T166", "Update Buyer Details", self.test_t166_update_buyer_details, skip=True)
        self.test_endpoint("T169", "Query Pump/Nozzle/Tank", self.test_t169_query_pump_nozzle_tank, skip=True)
        
        # Agent / USSD / Contacts
        print_section("AGENT / USSD / FREQUENT CONTACTS")
        self.test_endpoint("T175", "USSD Account Create", self.test_t175_ussd_account_create)
        self.test_endpoint("T178", "EFD Transfer", self.test_t178_efd_transfer)
        self.test_endpoint("T181", "Upload Frequent Contacts", self.test_t181_upload_frequent_contacts)
        self.test_endpoint("T182", "Get Frequent Contacts", self.test_t182_get_frequent_contacts)
        
        # Export / Customs
        print_section("EXPORT / CUSTOMS OPERATIONS")
        self.test_endpoint("T187", "Query FDN Status", self.test_t187_query_fdn_status)
        
        # Reporting & System
        print_section("REPORTING & SYSTEM OPERATIONS")
        self.test_endpoint("T116", "Z-Report Upload", self.test_t116_z_report_upload)
        self.test_endpoint("T132", "Upload Exception Logs", self.test_t132_upload_exception_logs)
        self.test_endpoint("T133", "TCS Upgrade Download", self.test_t133_tcs_upgrade_download)
        self.test_endpoint("T135", "Get TCS Latest Version", self.test_t135_get_tcs_latest_version)
        self.test_endpoint("T136", "Certificate Upload", self.test_t136_certificate_upload, skip=True)
        
        # Detail queries that need IDs (run last)
        print_section("DETAIL QUERIES (REQUIRE PRIOR IDs)")
        self.test_endpoint("T148", "Stock Record Detail", self.test_t148_stock_records_detail, skip=True)
        self.test_endpoint("T160", "Stock Adjust Detail", self.test_t160_stock_adjust_detail, skip=True)
        self.test_endpoint("T184", "Stock Transfer Detail", self.test_t184_stock_transfer_detail, skip=True)
        
        # Print Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print_section("TEST SUMMARY")
        print(f"✅ Passed:  {len(self.results['passed'])}")
        print(f"❌ Failed:  {len(self.results['failed'])}")
        print(f"⚠️  Skipped: {len(self.results['skipped'])}")
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['skipped'])
        print(f"📊 Total:   {total}")
        
        if self.results["failed"]:
            print("\n❌ Failed Endpoints:")
            for code in self.results["failed"]:
                print(f"  - {code}")
        
        if self.results["skipped"]:
            print("\n⚠️  Skipped Endpoints:")
            for code in self.results["skipped"]:
                print(f"  - {code}")
        
        print(f"\n✅ Passed Endpoints ({len(self.results['passed'])}):")
        for code in sorted(self.results['passed']):
            print(f"  ✓ {code}")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return exit code
        return 0 if not self.results["failed"] else 1


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main entry point."""
    print("=" * 80)
    print("  EFRIS API COMPLETE ENDPOINT INTEGRATION TEST")
    print("=" * 80)
    
    # Load configuration
    print("\nLoading configuration...")
    try:
        config = load_config_from_env(prefix="EFRIS")
        validate_config(config)
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nRequired environment variables:")
        print("  EFRIS_ENV=sbx|prod")
        print("  EFRIS_TIN=your_tin")
        print("  EFRIS_DEVICE_NO=your_device")
        print("  EFRIS_PFX_PATH=/path/to/cert.pfx")
        print("  EFRIS_PFX_PASSWORD=your_password")
        print("  EFRIS_TAXPAYER_ID=1")
        sys.exit(1)
    
    # Handle password (may be bytes from env)
    password = config["pfx_password"]
    if isinstance(password, bytes):
        password = password.decode()
    
    # Initialize clients
    print("\nInitializing clients...")
    try:
        key_client = KeyClient(
            pfx_path=config["pfx_path"],
            password=password,
            tin=config["tin"],
            device_no=config["device_no"],
            brn=config.get("brn", ""),
            sandbox=config["env"] == "sbx",
            timeout=config.get("http", {}).get("timeout", 30),
            taxpayer_id=config.get("taxpayer_id", '1')
        )
        print("✅ KeyClient initialized")
    except Exception as e:
        print(f"❌ KeyClient error: {e}")
        sys.exit(1)
    
    try:
        client = Client(config=config, key_client=key_client)
        print("✅ Client initialized")
    except Exception as e:
        print(f"❌ Client error: {e}")
        sys.exit(1)
    
    # Run tests
    print("\n" + "=" * 80)
    tester = EfrisEndpointTester(client=client, key_client=key_client, config=config)
    exit_code = tester.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()