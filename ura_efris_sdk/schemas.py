from typing import List, Optional, Union, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Annotated
import re


# =========================================================
# COMMON CONSTRAINED TYPES (URA v1.5 Spec)
# =========================================================

TIN = Annotated[str, Field(min_length=10, max_length=10, pattern=r"^[A-Z0-9]{10}$")]
NIN_BRN = Annotated[str, Field(min_length=1, max_length=50)]
DEVICE_NO = Annotated[str, Field(min_length=1, max_length=50)]
YN = Annotated[str, Field(pattern=r"^[YN]$")]
DT14 = Annotated[str, Field(pattern=r"^\d{14}$")]
DT8 = Annotated[str, Field(pattern=r"^\d{8}$")]
FLEX_DATE = Annotated[str, Field(min_length=8, max_length=14)]
CODE_3 = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[0-9]{3}$")]
CODE_5 = Annotated[str, Field(min_length=1, max_length=5, pattern=r"^[A-Z0-9]{1,5}$")]
CODE_10 = Annotated[str, Field(min_length=1, max_length=10, pattern=r"^[A-Z0-9]{1,10}$")]
AMOUNT_18_2 = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
AMOUNT_13_2 = Annotated[Decimal, Field(ge=0, max_digits=13, decimal_places=2)]
RATE_7_2 = Annotated[Decimal, Field(ge=0, le=100, max_digits=7, decimal_places=2)]
RATE_5_2 = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
TAX_CATEGORY = Annotated[str, Field(pattern=r"^[ABCDE]$")]
BUYER_TYPE = Annotated[str, Field(pattern=r"^[0123]$")]
INVOICE_TYPE = Annotated[str, Field(pattern=r"^[0123]$")]
PAYMENT_MODE = Annotated[str, Field(pattern=r"^10[1-9]|110$")]
OPERATION_TYPE = Annotated[str, Field(pattern=r"^10[12]$")]


# =========================================================
# T109: BILLING UPLOAD
# =========================================================

class T109GoodsItem(BaseModel):
    goodsCode: Annotated[str, Field(min_length=1, max_length=50)]
    goodsName: Annotated[str, Field(min_length=1, max_length=200)]
    model: Optional[Annotated[str, Field(max_length=50)]] = None
    unit: Annotated[str, Field(min_length=1, max_length=20)]
    qty: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]
    unitPrice: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
    amount: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
    taxRate: Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
    taxAmount: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
    discountFlag: Annotated[str, Field(pattern=r"^[012]$")] = "0"
    discountAmount: Optional[Annotated[Decimal, Field(ge=0)]] = None
    taxCategory: Optional[TAX_CATEGORY] = None
    goodsCategoryId: Optional[Annotated[str, Field(max_length=20)]] = None
    
    @model_validator(mode="after")
    def validate_amounts(self) -> "T109GoodsItem":
        calculated = self.qty * self.unitPrice
        if abs(calculated - self.amount) > Decimal("0.01"):
            raise ValueError(
                f"Item amount mismatch: qty({self.qty}) * unitPrice({self.unitPrice}) = {calculated} ≠ amount({self.amount})"
            )
        return self


class T109BillingUpload(BaseModel):
    invoiceType: INVOICE_TYPE
    invoiceNo: Annotated[str, Field(min_length=1, max_length=50)]
    invoiceDate: DT8
    buyerType: BUYER_TYPE
    sellerTin: TIN
    sellerBranchNo: Annotated[str, Field(min_length=1, max_length=50)]
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "UGX"
    goodsDetails: List[T109GoodsItem]
    totalAmount: AMOUNT_18_2
    totalTaxAmount: AMOUNT_18_2
    buyerTin: Optional[TIN] = None
    buyerLegalName: Optional[Annotated[str, Field(max_length=200)]] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerContactNumber: Optional[Annotated[str, Field(max_length=20)]] = None
    exchangeRate: Optional[Annotated[Decimal, Field(gt=0)]] = None
    payWay: Optional[List[dict]] = None
    operatorName: Annotated[str, Field(min_length=1, max_length=60)]
    referenceNo: Optional[Annotated[str, Field(max_length=50)]] = None
    remarks: Optional[Annotated[str, Field(max_length=400)]] = None
    
    @field_validator("invoiceNo")
    @classmethod
    def no_leading_zeros(cls, v: str) -> str:
        if v != "0" and v.startswith("0"):
            raise ValueError("Invoice number must not have leading zeros")
        return v
    
    @model_validator(mode="after")
    def validate_b2b_b2g_fields(self) -> "T109BillingUpload":
        if self.buyerType in ["0", "3"]:
            if not self.buyerTin:
                raise ValueError("buyerTin is required for B2B/B2G transactions")
            if not self.buyerLegalName:
                raise ValueError("buyerLegalName is required for B2B/B2G transactions")
        return self
    
    @model_validator(mode="after")
    def validate_totals(self) -> "T109BillingUpload":
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
# OTHER SCHEMAS
# =========================================================

class T108InvoiceDetails(BaseModel):
    invoiceNo: Annotated[str, Field(min_length=1, max_length=50)]


class T107InvoiceQuery(BaseModel):
    deviceNo: DEVICE_NO
    startDate: DT8
    endDate: DT8
    invoiceType: Optional[INVOICE_TYPE] = None
    buyerTin: Optional[TIN] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20


class T119QueryTaxpayer(BaseModel):
    tin: Optional[TIN] = None
    ninBrn: Optional[NIN_BRN] = None
    
    @model_validator(mode="after")
    def require_one_identifier(self) -> "T119QueryTaxpayer":
        if not self.tin and not self.ninBrn:
            raise ValueError("Either tin or ninBrn must be provided")
        return self


class T131StockItem(BaseModel):
    goodsCode: Annotated[str, Field(min_length=1, max_length=50)]
    measureUnit: Annotated[str, Field(min_length=1, max_length=20)]
    quantity: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]
    unitPrice: AMOUNT_18_2
    remarks: Optional[Annotated[str, Field(max_length=200)]] = None


class T131StockMaintain(BaseModel):
    operationType: OPERATION_TYPE
    stockInDate: DT8
    stockInType: Annotated[str, Field(pattern=r"^10[1234]$")]
    supplierTin: Optional[TIN] = None
    supplierName: Optional[Annotated[str, Field(max_length=200)]] = None
    remarks: Optional[Annotated[str, Field(max_length=200)]] = None
    goodsStockInItem: List[T131StockItem]


# =========================================================
# VALIDATOR SCHEMA MAP
# =========================================================

SCHEMAS = {
    "billing_upload": T109BillingUpload,
    "batch_invoice_upload": None,
    "invoice_details": T108InvoiceDetails,
    "invoice_query": T107InvoiceQuery,
    "credit_application": None,
    "credit_note_status": None,
    "query_taxpayer": T119QueryTaxpayer,
    "get_branches": None,
    "goods_upload": None,
    "goods_inquiry": None,
    "stock_maintain": T131StockMaintain,
    "query_stock": None,
    "get_symmetric_key": None,
    "test_interface": None,
}