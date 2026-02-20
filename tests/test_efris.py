#!/usr/bin/env python3
"""
EFRIS API Complete Endpoint Integration Test
=============================================
This script tests ALL endpoints from the EFRIS API documentation (T101-T144).
It's designed for integration testing, not unit testing.

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
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List

from ura_efris_sdk import (
    Client,
    KeyClient,
    load_config_from_env,
    validate_config
)
from ura_efris_sdk.exceptions import ApiException, ValidationException, EncryptionException


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
    if hasattr(error, 'error_code'):
        print(f"   Error Code: {error.error_code}")
    if hasattr(error, 'details'):
        print(f"   Details: {error.details}")


# =============================================================================
# MAIN TEST CLASS
# =============================================================================

class EfrisEndpointTester:
    """Tests all EFRIS API endpoints."""
    
    def __init__(self, client: Client, key_client: KeyClient):
        self.client = client
        self.key_client = key_client
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
            "business_key": None
        }
    
    def test_endpoint(self, code: str, name: str, test_func):
        """Run a single endpoint test and record results."""
        print_endpoint(code, name)
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
    # AUTHENTICATION & INITIALIZATION (T101-T105)
    # =========================================================================
    
    def test_t101_get_server_time(self):
        """T101 - Get Server Time (Test Connection)"""
        response = self.client.test_interface()
        print(response)
        server_time = response.get("data", {}).get("content", {}).get("currentTime")
        if not server_time:
            server_time = response.get("currentTime", "N/A")
        print(f"Server Time: {server_time}")
        return response
    
    def test_t102_client_init(self):
        """T102 - Client Initialization"""
        # Note: This returns whitebox keys which we don't use (we use PFX)
        response = self.client.client_init()
        print("Client initialization completed")
        return response
    
    def test_t103_sign_in(self):
        """T103 - Sign In (Login)"""
        response = self.client.sign_in()
        content = response.get("data", {}).get("content", {})
        if content:
            taxpayer = content.get("taxpayer", {})
            print(f"Taxpayer: {taxpayer.get('legalName', 'N/A')}")
            print(f"TIN: {taxpayer.get('tin', 'N/A')}")
            device = content.get("device", {})
            print(f"Device: {device.get('deviceNo', 'N/A')}")
        return response
    
    def test_t104_get_symmetric_key(self):
        """T104 - Get Symmetric Key (AES)"""
        response = self.client.get_symmetric_key(force=True)
        print(f"AES Key Status: {response.get('resultMsg', 'N/A')}")
        print(f"AES Key Valid Until: {self.key_client.aes_key_valid_until}")
        return response
    
    def test_t105_forget_password(self):
        """T105 - Forget Password (SKIP - Destructive)"""
        print("⚠️  SKIPPED - Password reset is destructive")
        self.results["skipped"].append("T105")
        return None
    
    # =========================================================================
    # INVOICE OPERATIONS (T106-T109, T129)
    # =========================================================================
    
    def test_t106_query_all_invoices(self):
        """T106 - Query All Invoices (Including Credit/Debit Notes)"""
        now = datetime.now()
        filters = {
            "startDate": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            "endDate": now.strftime("%Y-%m-%d"),
            "pageNo": 1,
            "pageSize": 10,
            "invoiceKind": "1"  # Invoice
        }
        response = self.client.query_all_invoices(filters)
        records = response.get("data", {}).get("content", {}).get("records", [])
        print(f"Found {len(records)} invoices")
        if records:
            self.context["invoice_no"] = records[0].get("invoiceNo")
            print(f"Sample Invoice No: {self.context['invoice_no']}")
        return response
    
    def test_t107_query_normal_invoices(self):
        """T107 - Query Normal Invoices (Eligible for Credit Notes)"""
        now = datetime.now()
        filters = {
            "startDate": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            "endDate": now.strftime("%Y-%m-%d"),
            "pageNo": 1,
            "pageSize": 10,
            "invoiceType": "1"  # Invoice only
        }
        response = self.client.query_invoices(filters)
        records = response.get("data", {}).get("content", {}).get("records", [])
        print(f"Found {len(records)} normal invoices")
        return response
    
    def test_t108_invoice_details(self):
        """T108 - Get Invoice Details"""
        invoice_no = self.context.get("invoice_no")
        if not invoice_no:
            print("⚠️  SKIPPED - No invoice number from previous test")
            self.results["skipped"].append("T108")
            return None
        
        response = self.client.verify_invoice(invoice_no)
        content = response.get("data", {}).get("content", {})
        basic_info = content.get("basicInformation", {})
        self.context["invoice_id"] = basic_info.get("invoiceId")
        print(f"Invoice ID: {self.context['invoice_id']}")
        print(f"Gross Amount: {content.get('summary', {}).get('grossAmount', 'N/A')}")
        return response
    
    def test_t109_upload_invoice(self):
        """T109 - Upload Invoice (Billing Upload)"""
        # Create a minimal test invoice
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        invoice_data = {
            "sellerDetails": {
                "tin": self.client.config["tin"],
                "legalName": "Test Company Ltd",
                "emailAddress": "test@example.com",
                "address": "Test Address",
                "mobilePhone": "256700000000"
            },
            "basicInformation": {
                "deviceNo": self.client.config["device_no"],
                "issuedDate": now,
                "operator": "admin",
                "currency": "UGX",
                "invoiceType": "1",  # Invoice
                "invoiceKind": "1",  # Invoice
                "dataSource": "103"  # WebService API
            },
            "buyerDetails": {
                "buyerTin": "1009830865",
                "buyerLegalName": "Test Buyer Ltd",
                "buyerType": "0",  # B2B
                "buyerEmail": "buyer@example.com"
            },
            "goodsDetails": [
                {
                    "item": "Test Product",
                    "itemCode": "TEST001",
                    "qty": Decimal("1.00"),
                    "unitOfMeasure": "101",  # kg
                    "unitPrice": Decimal("10000.00"),
                    "total": Decimal("10000.00"),
                    "taxRate": Decimal("0.18"),
                    "tax": Decimal("1800.00"),
                    "orderNumber": 0,
                    "discountFlag": "2",  # Normal
                    "deemedFlag": "2",  # Not deemed
                    "exciseFlag": "2",  # Not excise
                    "goodsCategoryId": "100000000",
                    "goodsCategoryName": "Standard"
                }
            ],
            "taxDetails": [
                {
                    "taxCategory": "Standard",
                    "netAmount": Decimal("10000.00"),
                    "taxRate": Decimal("0.18"),
                    "taxAmount": Decimal("1800.00"),
                    "grossAmount": Decimal("11800.00"),
                    "taxRateName": "18%"
                }
            ],
            "summary": {
                "netAmount": Decimal("10000.00"),
                "taxAmount": Decimal("1800.00"),
                "grossAmount": Decimal("11800.00"),
                "itemCount": 1,
                "modeCode": "1",  # Online
                "remarks": "Test invoice from integration test"
            },
            "payWay": [
                {
                    "paymentMode": "102",  # Cash
                    "paymentAmount": Decimal("11800.00"),
                    "orderNumber": "a"
                }
            ]
        }
        
        response = self.client.fiscalise_invoice(invoice_data)
        content = response.get("data", {}).get("content", {})
        basic_info = content.get("basicInformation", {})
        self.context["invoice_no"] = basic_info.get("invoiceNo")
        self.context["invoice_id"] = basic_info.get("invoiceId")
        print(f"Uploaded Invoice No: {self.context['invoice_no']}")
        print(f"Invoice ID: {self.context['invoice_id']}")
        return response
    
    def test_t129_batch_upload(self):
        """T129 - Batch Invoice Upload"""
        print("⚠️  SKIPPED - Requires pre-signed invoice content")
        self.results["skipped"].append("T129")
        return None
    
    # =========================================================================
    # CREDIT/DEBIT NOTE OPERATIONS (T110-T114, T118, T120, T122)
    # =========================================================================
    
    def test_t110_credit_note_application(self):
        """T110 - Apply for Credit Note"""
        invoice_id = self.context.get("invoice_id")
        invoice_no = self.context.get("invoice_no")
        
        if not invoice_id or not invoice_no:
            print("⚠️  SKIPPED - No invoice from previous test")
            self.results["skipped"].append("T110")
            return None
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        application_data = {
            "oriInvoiceId": invoice_id,
            "oriInvoiceNo": invoice_no,
            "reasonCode": "102",  # Cancellation of purchase
            "reason": "Integration test credit note",
            "applicationTime": now,
            "invoiceApplyCategoryCode": "101",  # Credit Note
            "currency": "UGX",
            "source": "103",  # WebService API
            "goodsDetails": [
                {
                    "item": "Test Product",
                    "itemCode": "TEST001",
                    "qty": Decimal("-1.00"),  # Negative for credit
                    "unitOfMeasure": "101",
                    "total": Decimal("-10000.00"),
                    "tax": Decimal("-1800.00"),
                    "orderNumber": 0,
                    "deemedFlag": "2",
                    "exciseFlag": "2",
                    "goodsCategoryId": "100000000",
                    "goodsCategoryName": "Standard"
                }
            ],
            "taxDetails": [
                {
                    "taxCategory": "Standard",
                    "netAmount": Decimal("10000.00"),
                    "taxRate": Decimal("0.18"),
                    "taxAmount": Decimal("1800.00"),
                    "grossAmount": Decimal("11800.00"),
                    "taxRateName": "18%"
                }
            ],
            "summary": {
                "netAmount": Decimal("-10000.00"),
                "taxAmount": Decimal("-1800.00"),
                "grossAmount": Decimal("-11800.00"),
                "itemCount": 1,
                "modeCode": "1"
            }
        }
        
        response = self.client.apply_credit_note(application_data)
        content = response.get("data", {}).get("content", {})
        self.context["reference_no"] = content.get("referenceNo")
        print(f"Credit Note Reference No: {self.context['reference_no']}")
        return response
    
    def test_t111_query_credit_note_status(self):
        """T111 - Query Credit/Debit Note Application Status"""
        filters = {
            "pageNo": 1,
            "pageSize": 10,
            "queryType": "1",  # Current user's applications
            "invoiceApplyCategoryCode": "101"  # Credit Note
        }
        response = self.client.query_credit_note_status(filters)
        records = response.get("data", {}).get("content", {}).get("records", [])
        print(f"Found {len(records)} credit note applications")
        if records:
            self.context["application_id"] = records[0].get("id")
            self.context["task_id"] = records[0].get("taskId")
            print(f"Sample Application ID: {self.context['application_id']}")
        return response
    
    def test_t112_credit_application_detail(self):
        """T112 - Get Credit Note Application Details"""
        application_id = self.context.get("application_id")
        if not application_id:
            print("⚠️  SKIPPED - No application ID from previous test")
            self.results["skipped"].append("T112")
            return None
        
        response = self.client.get_credit_application_detail(application_id)
        content = response.get("data", {}).get("content", {})
        print(f"Application Status: {content.get('approveStatusCode', 'N/A')}")
        return response
    
    def test_t113_approve_credit_note(self):
        """T113 - Approve/Reject Credit Note"""
        reference_no = self.context.get("reference_no")
        task_id = self.context.get("task_id")
        
        if not reference_no or not task_id:
            print("⚠️  SKIPPED - No reference number or task ID")
            self.results["skipped"].append("T113")
            return None
        
        response = self.client.approve_credit_note(
            reference_no=reference_no,
            approve=True,
            task_id=task_id,
            remark="Approved via integration test"
        )
        print("Credit note approval submitted")
        return response
    
    def test_t114_cancel_credit_note(self):
        """T114 - Cancel Credit/Debit Note Application"""
        invoice_id = self.context.get("invoice_id")
        invoice_no = self.context.get("invoice_no")
        
        if not invoice_id or not invoice_no:
            print("⚠️  SKIPPED - No invoice information")
            self.results["skipped"].append("T114")
            return None
        
        response = self.client.cancel_credit_note_application(
            ori_invoice_id=invoice_id,
            invoice_no=invoice_no,
            reason_code="102",
            reason="Integration test cancellation",
            cancel_type="104"  # Cancel Credit Note
        )
        print("Credit note cancellation submitted")
        return response
    
    def test_t118_query_credit_application_details(self):
        """T118 - Query Credit Note Application Details (Alternative)"""
        application_id = self.context.get("application_id")
        if not application_id:
            print("⚠️  SKIPPED - No application ID")
            self.results["skipped"].append("T118")
            return None
        
        response = self.client.post("query_credit_application", {"id": application_id}, encrypt=True)
        print("Credit application details queried")
        return response
    
    def test_t120_void_application(self):
        """T120 - Void Credit/Debit Note Application"""
        reference_no = self.context.get("reference_no")
        if not reference_no:
            print("⚠️  SKIPPED - No reference number")
            self.results["skipped"].append("T120")
            return None
        
        # Generate a business key (usually from system)
        business_key = f"BK{int(time.time())}"
        self.context["business_key"] = business_key
        
        response = self.client.void_credit_debit_application(
            business_key=business_key,
            reference_no=reference_no
        )
        print("Application void submitted")
        return response
    
    def test_t122_query_invalid_credit(self):
        """T122 - Query Invalid Credit Note Details"""
        invoice_no = self.context.get("invoice_no")
        if not invoice_no:
            print("⚠️  SKIPPED - No invoice number")
            self.results["skipped"].append("T122")
            return None
        
        response = self.client.query_invalid_credit_note(invoice_no)
        print("Invalid credit note query completed")
        return response
    
    # =========================================================================
    # TAXPAYER & BRANCH OPERATIONS (T119, T137, T138)
    # =========================================================================
    
    def test_t119_query_taxpayer(self):
        """T119 - Query Taxpayer Information by TIN"""
        response = self.client.query_taxpayer_by_tin(tin=self.client.config["tin"])
        content = response.get("data", {}).get("content", {})
        taxpayer = content.get("taxpayer", {})
        print(f"Taxpayer Name: {taxpayer.get('legalName', 'N/A')}")
        print(f"TIN: {taxpayer.get('tin', 'N/A')}")
        return response
    
    def test_t137_check_taxpayer_type(self):
        """T137 - Check Taxpayer VAT Type"""
        response = self.client.check_taxpayer_type(tin=self.client.config["tin"])
        content = response.get("data", {}).get("content", {})
        print(f"Taxpayer Type: {content.get('taxpayerType', 'N/A')}")
        print(f"Is Exempt: {content.get('isExempt', 'N/A')}")
        return response
    
    def test_t138_get_branches(self):
        """T138 - Get Registered Branches"""
        response = self.client.get_registered_branches(tin=self.client.config["tin"])
        content = response.get("data", {}).get("content", {})
        branches = content.get("branches", [])
        print(f"Found {len(branches)} branches")
        return response
    
    # =========================================================================
    # COMMODITY & EXCISE OPERATIONS (T115, T123-T125, T134)
    # =========================================================================
    
    def test_t115_system_dictionary(self):
        """T115 - System Dictionary Update"""
        response = self.client.update_system_dictionary()
        content = response.get("data", {}).get("content", {})
        print(content)
        print(f"Currency Types: {len(content.get('currencyType', []))}")
        print(f"Tax Types: {len(content.get('taxType', []))}")
        return response
    
    def test_t123_query_commodity_categories(self):
        """T123 - Query All Commodity Categories"""
        response = self.client.query_commodity_categories_all()
        categories = response.get("data", {}).get("content", [])
        print(f"Found {len(categories)} commodity categories")
        return response
    
    def test_t124_query_commodity_categories_page(self):
        """T124 - Query Commodity Categories (Paginated)"""
        response = self.client.query_commodity_categories(page_no=1, page_size=10)
        content = response.get("data", {}).get("content", {})
        records = content.get("records", [])
        print(f"Page 1: {len(records)} categories")
        return response
    
    def test_t125_query_excise_duty(self):
        """T125 - Query Excise Duty Codes"""
        response = self.client.query_excise_duty_codes()
        content = response.get("data", {}).get("content", {})
        excise_list = content.get("exciseDutyList", [])
        print(f"Found {len(excise_list)} excise duty codes")
        return response
    
    def test_t134_commodity_incremental(self):
        """T134 - Commodity Category Incremental Update"""
        response = self.client.sync_commodity_categories(local_version="1.0")
        categories = response.get("data", {}).get("content", [])
        print(f"Updated {len(categories)} categories")
        return response
    
    # =========================================================================
    # EXCHANGE RATE OPERATIONS (T121, T126)
    # =========================================================================
    
    def test_t121_get_exchange_rate(self):
        """T121 - Get Exchange Rate for Currency"""
        response = self.client.get_exchange_rate(currency="USD")
        content = response.get("data", {}).get("content", {})
        print(f"USD Rate: {content.get('rate', 'N/A')} UGX")
        return response
    
    def test_t126_get_all_exchange_rates(self):
        """T126 - Get All Exchange Rates"""
        response = self.client.get_all_exchange_rates()
        rates = response.get("data", {}).get("content", [])
        print(f"Found {len(rates)} exchange rates")
        for rate in rates[:5]:  # Show first 5
            print(f"  {rate.get('currency')}: {rate.get('rate')}")
        return response
    
    # =========================================================================
    # GOODS & STOCK OPERATIONS (T127, T128, T130, T131, T139, T144)
    # =========================================================================
    
    def test_t130_upload_goods(self):
        """T130 - Upload Goods"""
        goods_data = [
            {
                "goodsName": "Test Product Integration",
                "goodsCode": f"TEST{int(time.time())}",
                "measureUnit": "101",  # kg
                "unitPrice": Decimal("10000.00"),
                "currency": "UGX",
                "commodityCategoryId": "100000000",
                "haveExciseTax": "102",  # No excise
                "stockPrewarning": 10
            }
        ]
        response = self.client.upload_goods(goods_data)
        results = response.get("data", {}).get("content", [])
        if results:
            self.context["goods_code"] = results[0].get("goodsCode")
            print(f"Uploaded Goods Code: {self.context['goods_code']}")
        return response
    
    def test_t127_inquire_goods(self):
        """T127 - Goods/Services Inquiry"""
        filters = {
            "pageNo": 1,
            "pageSize": 10
        }
        response = self.client.inquire_goods(filters)
        content = response.get("data", {}).get("content", {})
        records = content.get("records", [])
        print(f"Found {len(records)} goods")
        if records:
            self.context["goods_id"] = records[0].get("id")
            print(f"Sample Goods ID: {self.context['goods_id']}")
        return response
    
    def test_t144_query_goods_by_code(self):
        """T144 - Query Goods by Code"""
        goods_code = self.context.get("goods_code")
        if not goods_code:
            print("⚠️  SKIPPED - No goods code from previous test")
            self.results["skipped"].append("T144")
            return None
        
        response = self.client.query_goods_by_code(goods_code=goods_code)
        content = response.get("data", {}).get("content", {})
        print(f"Goods Name: {content.get('goodsName', 'N/A')}")
        return response
    
    def test_t128_query_stock(self):
        """T128 - Query Stock Quantity by Goods ID"""
        goods_id = self.context.get("goods_id")
        if not goods_id:
            print("⚠️  SKIPPED - No goods ID from previous test")
            self.results["skipped"].append("T128")
            return None
        
        response = self.client.query_stock_quantity(goods_id=goods_id)
        content = response.get("data", {}).get("content", {})
        print(f"Stock: {content.get('stock', 'N/A')}")
        print(f"Pre-warning: {content.get('stockPrewarning', 'N/A')}")
        return response
    
    def test_t131_maintain_stock(self):
        """T131 - Goods Stock Maintain"""
        goods_id = self.context.get("goods_id")
        if not goods_id:
            print("⚠️  SKIPPED - No goods ID")
            self.results["skipped"].append("T131")
            return None
        
        stock_data = {
            "operationType": "101",  # Stock In
            "stockInDate": datetime.now().strftime("%Y-%m-%d"),
            "stockInType": "101",  # Purchase
            "goodsStockInItem": [
                {
                    "commodityGoodsId": goods_id,
                    "quantity": Decimal("100.00"),
                    "unitPrice": Decimal("10000.00")
                }
            ]
        }
        response = self.client.maintain_stock(stock_data)
        results = response.get("data", {}).get("content", [])
        print(f"Stock maintenance completed for {len(results)} items")
        return response
    
    def test_t139_transfer_stock(self):
        """T139 - Stock Transfer Between Branches"""
        goods_id = self.context.get("goods_id")
        if not goods_id:
            print("⚠️  SKIPPED - No goods ID")
            self.results["skipped"].append("T139")
            return None
        
        transfer_data = {
            "transferDate": datetime.now().strftime("%Y-%m-%d"),
            "transferType": "101",  # Transfer Out
            "goodsTransferItem": [
                {
                    "commodityGoodsId": goods_id,
                    "quantity": Decimal("10.00"),
                    "unitPrice": Decimal("10000.00"),
                    "fromBranch": "01",
                    "toBranch": "02"
                }
            ]
        }
        response = self.client.transfer_stock(transfer_data)
        content = response.get("data", {}).get("content", {})
        print(f"Transfer Reference: {content.get('referenceNo', 'N/A')}")
        return response
    
    # =========================================================================
    # REPORTING & LOGGING (T116, T117, T132)
    # =========================================================================
    
    def test_t116_z_report_upload(self):
        """T116 - Z-Report Daily Upload"""
        report_data = {
            "deviceNo": self.client.config["device_no"],
            "reportDate": datetime.now().strftime("%Y-%m-%d"),
            "totalInvoices": 10,
            "totalAmount": Decimal("118000.00"),
            "totalTax": Decimal("18000.00")
        }
        response = self.client.upload_z_report(report_data)
        print("Z-report upload completed")
        return response
    
    def test_t117_invoice_checks(self):
        """T117 - Invoice Reconciliation/Checks"""
        invoice_no = self.context.get("invoice_no")
        if not invoice_no:
            print("⚠️  SKIPPED - No invoice number")
            self.results["skipped"].append("T117")
            return None
        
        invoice_checks = [
            {"invoiceNo": invoice_no, "invoiceType": "1"}
        ]
        response = self.client.verify_invoices_batch(invoice_checks)
        results = response.get("data", {}).get("content", [])
        print(f"Checked {len(results)} invoices")
        return response
    
    def test_t132_upload_exception_logs(self):
        """T132 - Upload Exception Logs"""
        logs = [
            {
                "interruptionTypeCode": "101",  # Disconnected
                "description": "Integration test log",
                "errorDetail": "Test error detail",
                "interruptionTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
        response = self.client.upload_exception_logs(logs)
        print("Exception logs uploaded")
        return response
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Execute all endpoint tests in order."""
        print_section("EFRIS API COMPLETE ENDPOINT TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {self.client.config.get('env', 'unknown')}")
        print(f"TIN: {self.client.config.get('tin', 'unknown')}")
        print(f"Device: {self.client.config.get('device_no', 'unknown')}")
        
        # Authentication & Initialization
        print_section("AUTHENTICATION & INITIALIZATION")
        self.test_endpoint("T101", "Get Server Time", self.test_t101_get_server_time)
        self.test_endpoint("T102", "Client Initialization", self.test_t102_client_init)
        self.test_endpoint("T103", "Sign In", self.test_t103_sign_in)
        self.test_endpoint("T104", "Get Symmetric Key", self.test_t104_get_symmetric_key)
        self.test_endpoint("T105", "Forget Password", self.test_t105_forget_password)
        
        # Invoice Operations
        print_section("INVOICE OPERATIONS")
        self.test_endpoint("T106", "Query All Invoices", self.test_t106_query_all_invoices)
        self.test_endpoint("T107", "Query Normal Invoices", self.test_t107_query_normal_invoices)
        self.test_endpoint("T108", "Invoice Details", self.test_t108_invoice_details)
        self.test_endpoint("T109", "Upload Invoice", self.test_t109_upload_invoice)
        self.test_endpoint("T129", "Batch Invoice Upload", self.test_t129_batch_upload)
        
        # Credit/Debit Note Operations
        print_section("CREDIT/DEBIT NOTE OPERATIONS")
        self.test_endpoint("T110", "Credit Note Application", self.test_t110_credit_note_application)
        self.test_endpoint("T111", "Query Credit Note Status", self.test_t111_query_credit_note_status)
        self.test_endpoint("T112", "Credit Application Detail", self.test_t112_credit_application_detail)
        self.test_endpoint("T113", "Approve Credit Note", self.test_t113_approve_credit_note)
        self.test_endpoint("T114", "Cancel Credit Note", self.test_t114_cancel_credit_note)
        self.test_endpoint("T118", "Query Credit Application Details", self.test_t118_query_credit_application_details)
        self.test_endpoint("T120", "Void Application", self.test_t120_void_application)
        self.test_endpoint("T122", "Query Invalid Credit", self.test_t122_query_invalid_credit)
        
        # Taxpayer & Branch Operations
        print_section("TAXPAYER & BRANCH OPERATIONS")
        self.test_endpoint("T119", "Query Taxpayer by TIN", self.test_t119_query_taxpayer)
        self.test_endpoint("T137", "Check Taxpayer Type", self.test_t137_check_taxpayer_type)
        self.test_endpoint("T138", "Get Registered Branches", self.test_t138_get_branches)
        
        # Commodity & Excise Operations
        print_section("COMMODITY & EXCISE OPERATIONS")
        self.test_endpoint("T115", "System Dictionary", self.test_t115_system_dictionary)
        self.test_endpoint("T123", "Query Commodity Categories", self.test_t123_query_commodity_categories)
        self.test_endpoint("T124", "Query Categories (Paginated)", self.test_t124_query_commodity_categories_page)
        self.test_endpoint("T125", "Query Excise Duty", self.test_t125_query_excise_duty)
        self.test_endpoint("T134", "Commodity Incremental Update", self.test_t134_commodity_incremental)
        
        # Exchange Rate Operations
        print_section("EXCHANGE RATE OPERATIONS")
        self.test_endpoint("T121", "Get Exchange Rate", self.test_t121_get_exchange_rate)
        self.test_endpoint("T126", "Get All Exchange Rates", self.test_t126_get_all_exchange_rates)
        
        # Goods & Stock Operations
        print_section("GOODS & STOCK OPERATIONS")
        self.test_endpoint("T130", "Upload Goods", self.test_t130_upload_goods)
        self.test_endpoint("T127", "Inquire Goods", self.test_t127_inquire_goods)
        self.test_endpoint("T144", "Query Goods by Code", self.test_t144_query_goods_by_code)
        self.test_endpoint("T128", "Query Stock Quantity", self.test_t128_query_stock)
        self.test_endpoint("T131", "Maintain Stock", self.test_t131_maintain_stock)
        self.test_endpoint("T139", "Transfer Stock", self.test_t139_transfer_stock)
        
        # Reporting & Logging
        print_section("REPORTING & LOGGING")
        self.test_endpoint("T116", "Z-Report Upload", self.test_t116_z_report_upload)
        self.test_endpoint("T117", "Invoice Checks", self.test_t117_invoice_checks)
        self.test_endpoint("T132", "Upload Exception Logs", self.test_t132_upload_exception_logs)
        
        # Print Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print_section("TEST SUMMARY")
        print(f"✅ Passed:  {len(self.results['passed'])}")
        print(f"❌ Failed:  {len(self.results['failed'])}")
        print(f"⚠️  Skipped: {len(self.results['skipped'])}")
        print(f"📊 Total:   {len(self.results['passed']) + len(self.results['failed']) + len(self.results['skipped'])}")
        
        if self.results["failed"]:
            print("\nFailed Endpoints:")
            for code in self.results["failed"]:
                print(f"  - {code}")
        
        if self.results["skipped"]:
            print("\nSkipped Endpoints:")
            for code in self.results["skipped"]:
                print(f"  - {code}")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


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
            timeout=config.get("http", {}).get("timeout", 30)
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
    tester = EfrisEndpointTester(client=client, key_client=key_client)
    tester.run_all_tests()
    
    # Exit with appropriate code
    if tester.results["failed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()