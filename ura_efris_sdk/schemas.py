from typing import List, Optional, Union, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Annotated
import re


# =========================================================
# COMMON CONSTRAINED TYPES (URA v1.5 Spec)
# =========================================================

# TIN: 11 chars, alphanumeric uppercase (URA v1.5, page 3)
TIN = Annotated[str, Field(min_length=10, max_length=10, pattern=r"^[A-Z0-9]{10}$")]

# NIN/BRN: variable length
NIN_BRN = Annotated[str, Field(min_length=1, max_length=50)]

# Device/Branch ID: assigned by URA
DEVICE_NO = Annotated[str, Field(min_length=1, max_length=50)]

# Yes/No flag
YN = Annotated[str, Field(pattern=r"^[YN]$")]

# Date formats (URA v1.5, page 16)
DT14 = Annotated[str, Field(pattern=r"^\d{14}$")]  # yyyyMMddHHmmss
DT8 = Annotated[str, Field(pattern=r"^\d{8}$")]    # yyyyMMdd
FLEX_DATE = Annotated[str, Field(min_length=8, max_length=14)]

# Code fields
CODE_3 = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[0-9]{3}$")]
CODE_5 = Annotated[str, Field(min_length=1, max_length=5, pattern=r"^[A-Z0-9]{1,5}$")]
CODE_10 = Annotated[str, Field(min_length=1, max_length=10, pattern=r"^[A-Z0-9]{1,10}$")]

# Amounts (UGX) - URA v1.5, page 17
AMOUNT_18_2 = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
AMOUNT_13_2 = Annotated[Decimal, Field(ge=0, max_digits=13, decimal_places=2)]

# Tax rates (0-100%)
RATE_7_2 = Annotated[Decimal, Field(ge=0, le=100, max_digits=7, decimal_places=2)]
RATE_5_2 = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]

# Tax Categories (URA v1.5, page 3)
# A - Standard rate (18%)
# B - Zero (0%)
# C - Exempt (Not taxable)
# D - Deemed rate (18%)
# E - Excise Duty rate
TAX_CATEGORY = Annotated[str, Field(pattern=r"^[ABCDE]$")]

# Buyer Types (URA v1.5, page 8)
# 0: B2B, 1: B2C, 2: Foreigner, 3: B2G
BUYER_TYPE = Annotated[str, Field(pattern=r"^[0123]$")]

# Invoice Types (URA v1.5, page 13)
# 0: Normal, 1: Credit, 2: Debit, 3: Correction
INVOICE_TYPE = Annotated[str, Field(pattern=r"^[0123]$")]

# Payment Modes (URA v1.5, page 14)
PAYMENT_MODE = Annotated[str, Field(pattern=r"^10[1-9]|110$")]

# Operation Types (for stock)
OPERATION_TYPE = Annotated[str, Field(pattern=r"^10[12]$")]  # 101=New, 102=Update


# =========================================================
# T109: BILLING UPLOAD (Most Critical - URA v1.5, page 12-19)
# =========================================================

class T109GoodsItem(BaseModel):
    """Individual line item for T109 billing upload (URA v1.5, page 13-14)"""
    goodsCode: Annotated[str, Field(min_length=1, max_length=50)]
    goodsName: Annotated[str, Field(min_length=1, max_length=200)]
    model: Optional[Annotated[str, Field(max_length=50)]] = None
    unit: Annotated[str, Field(min_length=1, max_length=20)]
    qty: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]
    unitPrice: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
    amount: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
    taxRate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
    taxAmount: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
    discountFlag: Annotated[str, Field(pattern=r"^[012]$")] = "0"  # 0=No, 1=Yes, 2=Not applicable
    discountAmount: Optional[Annotated[Decimal, Field(ge=0)]] = None
    taxCategory: Optional[TAX_CATEGORY] = None
    goodsCategoryId: Optional[Annotated[str, Field(max_length=20)]] = None
    
    @model_validator(mode="after")
    def validate_amounts(self) -> "T109GoodsItem":
        """Business rule: amount should equal qty * unitPrice (with tolerance)"""
        calculated = self.qty * self.unitPrice
        if abs(calculated - self.amount) > Decimal("0.01"):
            raise ValueError(
                f"Item amount mismatch: qty({self.qty}) * unitPrice({self.unitPrice}) = {calculated} ≠ amount({self.amount})"
            )
        return self


class T109BillingUpload(BaseModel):
    """
    Request model for T109: Billing Upload (Fiscalise Invoice)
    Per URA v1.5 Integration Requirements (page 12-19)
    """
    # === REQUIRED FIELDS (URA v1.5, page 13-14) ===
    invoiceType: INVOICE_TYPE
    invoiceNo: Annotated[str, Field(min_length=1, max_length=50)]  # From taxpayer system (unique per v1.5)
    invoiceDate: DT8  # yyyyMMdd
    buyerType: BUYER_TYPE
    sellerTin: TIN
    sellerBranchNo: Annotated[str, Field(min_length=1, max_length=50)]
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "UGX"
    goodsDetails: List[T109GoodsItem]
    totalAmount: AMOUNT_18_2
    totalTaxAmount: AMOUNT_18_2
    
    # === CONDITIONAL FIELDS (B2B/B2G require buyer details) ===
    buyerTin: Optional[TIN] = None  # Required for B2B/B2G (URA v1.5, page 13)
    buyerLegalName: Optional[Annotated[str, Field(max_length=200)]] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerContactNumber: Optional[Annotated[str, Field(max_length=20)]] = None
    exchangeRate: Optional[Annotated[Decimal, Field(gt=0)]] = None  # Required if currency != UGX
    payWay: Optional[List[dict]] = None  # Payment methods
    operatorName: Annotated[str, Field(min_length=1, max_length=60)]
    referenceNo: Optional[Annotated[str, Field(max_length=50)]] = None  # From taxpayer system
    remarks: Optional[Annotated[str, Field(max_length=400)]] = None
    
    @field_validator("invoiceNo")
    @classmethod
    def no_leading_zeros(cls, v: str) -> str:
        if v != "0" and v.startswith("0"):
            raise ValueError("Invoice number must not have leading zeros")
        return v
    
    @model_validator(mode="after")
    def validate_b2b_b2g_fields(self) -> "T109BillingUpload":
        """B2B/B2G transactions require buyerTin + buyerLegalName (URA v1.5, page 13)"""
        if self.buyerType in ["0", "3"]:  # B2B or B2G
            if not self.buyerTin:
                raise ValueError("buyerTin is required for B2B/B2G transactions")
            if not self.buyerLegalName:
                raise ValueError("buyerLegalName is required for B2B/B2G transactions")
        return self
    
    @model_validator(mode="after")
    def validate_totals(self) -> "T109BillingUpload":
        """Validate header totals match item aggregates"""
        if not self.goodsDetails:
            raise ValueError("goodsDetails cannot be empty")
        
        calc_total = sum(item.amount for item in self.goodsDetails)
        calc_tax = sum(item.taxAmount for item in self.goodsDetails)
        
        tolerance = Decimal("0.01")
        if abs(calc_total - self.totalAmount) > tolerance:
            raise ValueError(f"totalAmount mismatch: items sum to {calc_total}, header says {self.totalAmount}")
        if abs(calc_tax - self.totalTaxAmount) > tolerance:
            raise ValueError(f"totalTaxAmount mismatch: items sum to {calc_tax}, header says {self.totalTaxAmount}")
        
        return self


# =========================================================
# T110: CREDIT NOTE APPLICATION (B2B/B2G only - URA v1.5, page 23)
# =========================================================

class T110CreditApplication(BaseModel):
    """Request for T110: Credit Note Application (URA v1.5, page 23)"""
    oriInvoiceId: Annotated[str, Field(min_length=1, max_length=50)]  # Original invoice ID
    oriInvoiceNo: Annotated[str, Field(min_length=1, max_length=50)]  # Original FDN
    reasonCode: Annotated[str, Field(pattern=r"^10[1-9]|110$")]  # Credit note reason code
    reason: Annotated[str, Field(max_length=400)]
    applicationTime: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")]
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "UGX"
    goodsDetails: List[T109GoodsItem]  # Reuse item schema (with negative values)
    taxDetails: Optional[List[dict]] = None
    summary: Optional[dict] = None
    buyerDetails: Optional[dict] = None
    payWay: Optional[List[dict]] = None
    remarks: Optional[Annotated[str, Field(max_length=400)]] = None
    
    @model_validator(mode="after")
    def validate_negative_amounts(self) -> "T110CreditApplication":
        """Credit note amounts should be negative"""
        for item in self.goodsDetails:
            if item.qty > 0 or item.amount > 0:
                raise ValueError("Credit note item quantities and amounts must be negative")
        return self


# =========================================================
# T119: QUERY TAXPAYER BY TIN (URA v1.5, page 7)
# =========================================================

class T119QueryTaxpayer(BaseModel):
    """Request for T119: Query Taxpayer Information By TIN"""
    tin: Optional[TIN] = None
    ninBrn: Optional[NIN_BRN] = None
    
    @model_validator(mode="after")
    def require_one_identifier(self) -> "T119QueryTaxpayer":
        if not self.tin and not self.ninBrn:
            raise ValueError("Either tin or ninBrn must be provided")
        return self


# =========================================================
# T130: GOODS UPLOAD (URA v1.5, page 7)
# =========================================================

class T130GoodsItem(BaseModel):
    """Item for T130: Goods Upload"""
    operationType: OPERATION_TYPE  # 101=new, 102=update
    goodsName: Annotated[str, Field(min_length=1, max_length=200)]
    goodsCode: Annotated[str, Field(min_length=1, max_length=50)]
    measureUnit: Annotated[str, Field(min_length=1, max_length=20)]
    unitPrice: AMOUNT_18_2
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "UGX"
    commodityCategoryId: Annotated[str, Field(min_length=1, max_length=20)]
    havePieceUnit: OPERATION_TYPE = "102"  # 101=Yes, 102=No
    pieceMeasureUnit: Optional[str] = None
    pieceUnitPrice: Optional[AMOUNT_18_2] = None
    haveOtherUnit: OPERATION_TYPE = "102"
    goodsOtherUnits: Optional[List[dict]] = None


class T130GoodsUpload(BaseModel):
    """Request for T130: Goods Upload"""
    goodsList: List[T130GoodsItem]
    operatorName: Annotated[str, Field(min_length=1, max_length=60)]


# =========================================================
# T131: STOCK MAINTAIN (URA v1.5, page 7)
# =========================================================

class T131StockItem(BaseModel):
    """Item for T131: Stock Maintain"""
    goodsCode: Annotated[str, Field(min_length=1, max_length=50)]
    measureUnit: Annotated[str, Field(min_length=1, max_length=20)]
    quantity: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]
    unitPrice: AMOUNT_18_2
    remarks: Optional[Annotated[str, Field(max_length=200)]] = None


class T131StockMaintain(BaseModel):
    """Request for T131: Stock Maintain"""
    operationType: OPERATION_TYPE  # 101=Stock In, 102=Stock Adjustment
    stockInDate: DT8
    stockInType: Annotated[str, Field(pattern=r"^10[1234]$")]  # Stock in type
    supplierTin: Optional[TIN] = None
    supplierName: Optional[Annotated[str, Field(max_length=200)]] = None
    remarks: Optional[Annotated[str, Field(max_length=200)]] = None
    goodsStockInItem: List[T131StockItem]


# =========================================================
# T107/T108: INVOICE QUERY & DETAILS (URA v1.5, page 9)
# =========================================================

class T107InvoiceQuery(BaseModel):
    """Request for T107: Invoice/Receipt Query"""
    deviceNo: DEVICE_NO
    startDate: DT8
    endDate: DT8
    invoiceType: Optional[INVOICE_TYPE] = None
    buyerTin: Optional[TIN] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20


class T108InvoiceDetails(BaseModel):
    """Request for T108: Invoice Details (verify by FDN)"""
    invoiceNo: Annotated[str, Field(min_length=1, max_length=50)]  # FDN


# =========================================================
# RESPONSE MODELS (Common Structure)
# =========================================================

class EfrisSuccessResponse(BaseModel):
    """Standard success response envelope"""
    returnCode: Annotated[str, Field(min_length=3, max_length=3)]
    returnMessage: Annotated[str, Field(max_length=500)]
    data: Optional[dict] = None


# =========================================================
# VALIDATOR SCHEMA MAP
# =========================================================

SCHEMAS = {
    # Invoice Management
    "billing_upload": T109BillingUpload,
    "batch_invoice_upload": None,
    "invoice_details": T108InvoiceDetails,
    "invoice_query": T107InvoiceQuery,
    
    # Credit/Debit Notes
    "credit_application": T110CreditApplication,
    "credit_note_status": None,
    
    # Registration
    "query_taxpayer": T119QueryTaxpayer,
    "get_branches": None,
    
    # Stock Management
    "goods_upload": T130GoodsUpload,
    "goods_inquiry": None,
    "stock_maintain": T131StockMaintain,
    "query_stock": None,
    
    # System
    "get_symmetric_key": None,
    "test_interface": None,
}