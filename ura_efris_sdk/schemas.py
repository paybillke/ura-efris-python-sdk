from typing import List, Optional, Union, Literal, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime
from typing_extensions import Annotated
from pydantic import RootModel
import re

# =========================================================
# COMMON CONSTRAINED TYPES (URA v1.0 Spec - Strict Validation)
# =========================================================

# TIN: 10 alphanumeric uppercase
TIN = Annotated[str, Field(min_length=10, max_length=20, pattern=r"^[A-Z0-9]{10,20}$")]

# NIN/BRN: 1-100 chars
NIN_BRN = Annotated[str, Field(min_length=1, max_length=100)]

# Device No: 1-20 chars
DEVICE_NO = Annotated[str, Field(min_length=1, max_length=20)]

# Yes/No flags
YN = Annotated[str, Field(pattern=r"^[YN]$")]

# Date formats per URA spec
DT8 = Annotated[str, Field(pattern=r"^\d{8}$")]  # YYYYMMDD
DT14 = Annotated[str, Field(pattern=r"^\d{14}$")]  # YYYYMMDDHHmmss
DT_REQUEST = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")]  # yyyy-MM-dd HH:mm:ss
DT_RESPONSE = Annotated[str, Field(pattern=r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$")]  # dd/MM/yyyy HH:mm:ss
DATE_ONLY = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]  # yyyy-MM-dd

# Code patterns
CODE_1 = Annotated[str, Field(min_length=1, max_length=1, pattern=r"^[0-9A-Z]$")]
CODE_6 = Annotated[str, Field(min_length=1, max_length=6, pattern=r"^[0-9A-Z]{1,6}$")]
CODE_16 = Annotated[str, Field(min_length=1, max_length=16)]
CODE_18 = Annotated[str, Field(min_length=1, max_length=18)]
CODE_80 = Annotated[str, Field(min_length=1, max_length=80)]
CODE_500 = Annotated[str, Field(min_length=1, max_length=500)]
CODE_3 = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[0-9]{3}$")]
CODE_5 = Annotated[str, Field(min_length=1, max_length=5, pattern=r"^[A-Z0-9]{1,5}$")]
CODE_10 = Annotated[str, Field(min_length=1, max_length=10, pattern=r"^[A-Z0-9]{1,10}$")]
CODE_20 = Annotated[str, Field(min_length=1, max_length=20)]
CODE_32 = Annotated[str, Field(min_length=1, max_length=32)]  # UUID
CODE_50 = Annotated[str, Field(min_length=1, max_length=50)]
CODE_100 = Annotated[str, Field(min_length=1, max_length=100)]

# Amounts (Decimal with precision)
AMOUNT_16_2 = Annotated[Decimal, Field(ge=0, max_digits=16, decimal_places=2)]
AMOUNT_18_2 = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
AMOUNT_20_8 = Annotated[Decimal, Field(ge=0, max_digits=20, decimal_places=8)]
AMOUNT_SIGNED_16_2 = Annotated[Decimal, Field(max_digits=16, decimal_places=2)]  # Can be negative

# Rates
RATE_12_8 = Annotated[Decimal, Field(ge=0, le=100, max_digits=12, decimal_places=8)]
RATE_5_2 = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]

# Enum-like constrained strings
TAX_CATEGORY = Annotated[str, Field(pattern=r"^[ABCDE]$")]  # A=Standard, B=Zero, C=Exempt, D=Excise, E=Other
BUYER_TYPE = Annotated[str, Field(pattern=r"^[0123]$")]  # 0=B2B/B2G, 1=B2C, 2=Foreigner, 3=Other
INVOICE_TYPE = Annotated[str, Field(pattern=r"^[1234]$")]  # 1=Invoice, 2=Credit, 3=Temporary, 4=Debit
INVOICE_KIND = Annotated[str, Field(pattern=r"^[12]$")]  # 1=Invoice, 2=Receipt
DATA_SOURCE = Annotated[str, Field(pattern=r"^10[1-4]$")]  # 101=EFD, 102=CS, 103=WebService, 104=BS
INDUSTRY_CODE = Annotated[str, Field(pattern=r"^10[1-3]$")]  # 101=General, 102=Export, 103=Import
DISCOUNT_FLAG = Annotated[str, Field(pattern=r"^[012]$")]  # 0=Discount amount, 1=Discount item, 2=Normal
DEEMED_FLAG = Annotated[str, Field(pattern=r"^[12]$")]  # 1=Deemed, 2=Not deemed
EXCISE_FLAG = Annotated[str, Field(pattern=r"^[12]$")]  # 1=Excise, 2=Not excise
EXCISE_RULE = Annotated[str, Field(pattern=r"^[12]$")]  # 1=By rate, 2=By quantity
OPERATION_TYPE = Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Stock In, 102=Stock Out
STOCK_IN_TYPE = Annotated[str, Field(pattern=r"^10[1-4]$")]  # 101=Purchase, 102=Return, 103=Adjustment+, 104=Adjustment-
PAYMENT_MODE = Annotated[str, Field(pattern=r"^10[1-9]|110$")]  # 101-110 payment types
APPROVE_STATUS = Annotated[str, Field(pattern=r"^10[1-3]$")]  # 101=Approved, 102=Pending, 103=Rejected
REASON_CODE = Annotated[str, Field(pattern=r"^10[1-5]$")]  # Credit/Debit note reason codes
IS_LEAF_NODE = Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Yes, 102=No
ENABLE_STATUS = Annotated[str, Field(pattern=r"^[01]$")]  # 0=Disabled, 1=Enabled
EXCLUSION_TYPE = Annotated[str, Field(pattern=r"^[012]$")]  # 0=Zero, 1=Exempt, 2=No exclusion
HAVE_EXCISE = Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Yes, 102=No
STOCK_LIMIT = Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Restricted, 102=Unlimited

# Currency (3-letter ISO)
CURRENCY = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]

# UUID
UUID32 = Annotated[str, Field(min_length=32, max_length=32, pattern=r"^[a-fA-F0-9]{32}$")]

# =========================================================
# T101: GET SERVER TIME
# =========================================================

class T101Response(BaseModel):
    currentTime: DT_RESPONSE  # dd/MM/yyyy HH:mm:ss


# =========================================================
# T102: CLIENT INITIALIZATION
# =========================================================

class T102Response(BaseModel):
    clientPriKey: Annotated[str, Field(max_length=1000)]  # Encrypted private key
    serverPubKey: Annotated[str, Field(min_length=1)]  # Server public key
    keyTable: Annotated[str, Field(min_length=1)]  # White box decryption table


# =========================================================
# T103: SIGN IN / LOGIN
# =========================================================

class T103Device(BaseModel):
    deviceModel: CODE_20
    deviceNo: DEVICE_NO
    deviceStatus: CODE_3
    deviceType: CODE_1
    validPeriod: DT_RESPONSE
    offlineAmount: Annotated[str, Field(pattern=r"^\d+$")]
    offlineDays: Annotated[str, Field(pattern=r"^\d+$")]
    offlineValue: Annotated[str, Field(pattern=r"^\d+$")]


class T103Taxpayer(BaseModel):
    id: CODE_20
    tin: TIN
    ninBrn: NIN_BRN
    legalName: Annotated[str, Field(max_length=256)]
    businessName: Annotated[str, Field(max_length=256)]
    taxpayerStatusId: CODE_3
    taxpayerRegistrationStatusId: CODE_3
    taxpayerType: CODE_3
    businessType: CODE_3
    departmentId: CODE_6
    contactName: Annotated[str, Field(max_length=100)]
    contactEmail: Annotated[str, Field(max_length=50)]
    contactMobile: Annotated[str, Field(max_length=30)]
    contactNumber: Annotated[str, Field(max_length=30)]
    placeOfBusiness: Annotated[str, Field(max_length=500)]


class T103TaxpayerBranch(BaseModel):
    branchCode: CODE_10
    branchName: Annotated[str, Field(max_length=100)]
    branchType: CODE_3
    contactName: Annotated[str, Field(max_length=100)]
    contactEmail: Annotated[str, Field(max_length=50)]
    contactMobile: Annotated[str, Field(max_length=30)]
    contactNumber: Annotated[str, Field(max_length=30)]
    placeOfBusiness: Annotated[str, Field(max_length=500)]


class T103TaxType(BaseModel):
    taxTypeName: Annotated[str, Field(max_length=100)]
    taxTypeCode: CODE_3
    registrationDate: DT_RESPONSE
    cancellationDate: Optional[DT_RESPONSE] = None


class T103Response(BaseModel):
    device: T103Device
    taxpayer: T103Taxpayer
    taxpayerBranch: Optional[T103TaxpayerBranch] = None
    taxType: List[T103TaxType]
    dictionaryVersion: CODE_20
    issueTaxTypeRestrictions: Annotated[str, Field(pattern=r"^[01]$")]
    taxpayerBranchVersion: CODE_20
    commodityCategoryVersion: CODE_20
    exciseDutyVersion: CODE_20
    sellersLogo: Optional[Annotated[str, Field(max_length=10000)]] = None  # Base64
    whetherEnableServerStock: Annotated[str, Field(pattern=r"^[01]$")]
    goodsStockLimit: STOCK_LIMIT
    exportCommodityTaxRate: RATE_5_2
    exportInvoiceExciseDuty: Annotated[str, Field(pattern=r"^[01]$")]
    maxGrossAmount: Annotated[str, Field(pattern=r"^\d+$")]


# =========================================================
# T104: GET SYMMETRIC KEY
# =========================================================

class T104Response(BaseModel):
    passowrdDes: Annotated[str, Field(min_length=1)]  # Note: API typo - "passowrdDes"
    sign: Annotated[str, Field(min_length=1)]


# =========================================================
# T105: FORGET PASSWORD
# =========================================================

class T105Request(BaseModel):
    userName: Annotated[str, Field(min_length=1, max_length=20)]
    changedPassword: Annotated[str, Field(min_length=1, max_length=50)]


# =========================================================
# T106: INVOICE/RECEIPT QUERY (ALL TYPES)
# =========================================================

class T106Request(BaseModel):
    oriInvoiceNo: Optional[CODE_20] = None
    invoiceNo: Optional[CODE_20] = None
    deviceNo: Optional[DEVICE_NO] = None
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerLegalName: Optional[Annotated[str, Field(max_length=256)]] = None
    combineKeywords: Optional[Annotated[str, Field(max_length=20)]] = None
    invoiceType: Optional[INVOICE_TYPE] = None
    invoiceKind: Optional[INVOICE_KIND] = None
    isInvalid: Optional[YN] = None
    isRefund: Optional[Annotated[str, Field(pattern=r"^[012]$")]] = None
    startDate: Optional[DATE_ONLY] = None
    endDate: Optional[DATE_ONLY] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20
    referenceNo: Optional[CODE_50] = None


class T106Record(BaseModel):
    id: CODE_32
    invoiceNo: CODE_20
    oriInvoiceId: CODE_20
    oriInvoiceNo: CODE_20
    issuedDate: DT_RESPONSE
    buyerTin: Optional[TIN] = None
    buyerLegalName: Optional[Annotated[str, Field(max_length=256)]] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    currency: CURRENCY
    grossAmount: AMOUNT_16_2
    taxAmount: AMOUNT_16_2
    dataSource: DATA_SOURCE
    isInvalid: Optional[YN] = None
    isRefund: Optional[Annotated[str, Field(pattern=r"^[012]$")]] = None
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None


class T106Page(BaseModel):
    pageNo: int
    pageSize: int
    totalSize: int
    pageCount: int


class T106Response(BaseModel):
    page: T106Page
    records: List[T106Record]


# =========================================================
# T107: QUERY NORMAL INVOICE/RECEIPT (For Credit/Debit Notes)
# =========================================================

class T107Request(BaseModel):
    invoiceNo: Optional[CODE_20] = None
    deviceNo: Optional[DEVICE_NO] = None
    buyerTin: Optional[TIN] = None
    buyerLegalName: Optional[Annotated[str, Field(max_length=256)]] = None
    invoiceType: Optional[Annotated[str, Field(pattern=r"^[14]$")]] = None  # Only 1 or 4
    startDate: Optional[DATE_ONLY] = None
    endDate: Optional[DATE_ONLY] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20


class T107Record(BaseModel):
    id: CODE_32
    invoiceNo: CODE_20
    oriInvoiceId: CODE_20
    oriInvoiceNo: CODE_20
    issuedDate: DT_RESPONSE
    buyerTin: TIN
    buyerBusinessName: Annotated[str, Field(max_length=256)]
    buyerLegalName: Annotated[str, Field(max_length=256)]
    tin: TIN
    businessName: Annotated[str, Field(max_length=256)]
    legalName: Annotated[str, Field(max_length=256)]
    currency: CURRENCY
    grossAmount: AMOUNT_16_2
    dataSource: DATA_SOURCE


class T107Response(BaseModel):
    page: T106Page
    records: List[T107Record]


# =========================================================
# T108: INVOICE DETAILS
# =========================================================

class T108Request(BaseModel):
    invoiceNo: CODE_20


class T108SellerDetails(BaseModel):
    tin: TIN
    ninBrn: NIN_BRN
    passportNumber: Optional[CODE_20] = None
    legalName: Annotated[str, Field(max_length=256)]
    businessName: Annotated[str, Field(max_length=256)]
    address: Optional[Annotated[str, Field(max_length=500)]] = None
    mobilePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    linePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    emailAddress: Optional[Annotated[str, Field(max_length=50)]] = None
    placeOfBusiness: Optional[Annotated[str, Field(max_length=500)]] = None
    referenceNo: Optional[CODE_50] = None


class T108BasicInformation(BaseModel):
    invoiceId: CODE_32
    invoiceNo: CODE_20
    oriInvoiceNo: Optional[CODE_20] = None
    antifakeCode: Optional[CODE_20] = None
    deviceNo: DEVICE_NO
    issuedDate: DT_RESPONSE
    oriIssuedDate: Optional[DT_RESPONSE] = None
    oriGrossAmount: Optional[AMOUNT_16_2] = None
    operator: Annotated[str, Field(max_length=100)]
    currency: CURRENCY
    oriInvoiceId: Optional[CODE_20] = None
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    dataSource: DATA_SOURCE
    isInvalid: Optional[YN] = None
    isRefund: Optional[Annotated[str, Field(pattern=r"^[012]$")]] = None
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None


class T108BuyerDetails(BaseModel):
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerPassportNum: Optional[CODE_20] = None
    buyerLegalName: Optional[Annotated[str, Field(max_length=256)]] = None
    buyerBusinessName: Optional[Annotated[str, Field(max_length=256)]] = None
    buyerAddress: Optional[Annotated[str, Field(max_length=500)]] = None
    buyerEmail: Optional[Annotated[str, Field(max_length=50)]] = None
    buyerMobilePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    buyerLinePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    buyerPlaceOfBusi: Optional[Annotated[str, Field(max_length=500)]] = None
    buyerType: BUYER_TYPE
    buyerCitizenship: Optional[Annotated[str, Field(max_length=128)]] = None
    buyerSector: Optional[Annotated[str, Field(max_length=200)]] = None
    buyerReferenceNo: Optional[CODE_50] = None


class T108GoodsItem(BaseModel):
    item: Annotated[str, Field(max_length=100)]
    itemCode: CODE_50
    qty: Optional[AMOUNT_20_8] = None
    unitOfMeasure: CODE_3
    unitPrice: Optional[AMOUNT_20_8] = None
    total: AMOUNT_SIGNED_16_2
    taxRate: RATE_12_8
    tax: AMOUNT_SIGNED_16_2
    discountTotal: Optional[AMOUNT_SIGNED_16_2] = None
    discountTaxRate: Optional[RATE_12_8] = None
    orderNumber: Annotated[int, Field(ge=0)]
    discountFlag: DISCOUNT_FLAG
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[Annotated[str, Field(max_length=1024)]] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: Annotated[str, Field(max_length=100)]
    exciseRate: Optional[Annotated[str, Field(max_length=21)]] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[Annotated[str, Field(max_length=100)]] = None
    
    @model_validator(mode="after")
    def validate_discount_logic(self) -> "T108GoodsItem":
        if self.discountFlag == "0":  # Discount amount line
            if self.qty is not None or self.unitPrice is not None:
                raise ValueError("qty and unitPrice must be empty for discount amount lines")
            if self.total >= 0:
                raise ValueError("total must be negative for discount amount lines")
        elif self.discountFlag in ["1", "2"]:  # Normal or discount item
            if self.qty is None or self.unitPrice is None:
                raise ValueError("qty and unitPrice required for normal/discount items")
            if self.total <= 0 and self.discountFlag == "2":
                raise ValueError("total must be positive for normal items")
        return self


class T108TaxDetail(BaseModel):
    taxCategory: Annotated[str, Field(max_length=100)]
    netAmount: AMOUNT_16_2
    taxRate: RATE_12_8
    taxAmount: AMOUNT_16_2
    grossAmount: AMOUNT_16_2
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    taxRateName: Annotated[str, Field(max_length=100)]


class T108Summary(BaseModel):
    netAmount: AMOUNT_16_2
    taxAmount: AMOUNT_16_2
    grossAmount: AMOUNT_16_2
    oriGrossAmount: Optional[AMOUNT_16_2] = None
    itemCount: Annotated[int, Field(ge=1)]
    modeCode: Annotated[str, Field(pattern=r"^[01]$")]  # 0=Offline, 1=Online
    remarks: Optional[Annotated[str, Field(max_length=500)]] = None
    qrCode: Optional[CODE_500] = None


class T108PayWay(BaseModel):
    paymentMode: PAYMENT_MODE
    paymentAmount: AMOUNT_16_2
    orderNumber: Annotated[str, Field(min_length=1, max_length=10)]


class T108Extend(BaseModel):
    reason: Optional[Annotated[str, Field(max_length=1024)]] = None
    reasonCode: Optional[REASON_CODE] = None


class T108Custom(BaseModel):
    sadNumber: Optional[CODE_20] = None
    office: Optional[Annotated[str, Field(max_length=35)]] = None
    cif: Optional[Annotated[str, Field(max_length=50)]] = None
    wareHouseNumber: Optional[CODE_16] = None
    wareHouseName: Optional[Annotated[str, Field(max_length=256)]] = None
    destinationCountry: Optional[Annotated[str, Field(max_length=256)]] = None
    originCountry: Optional[Annotated[str, Field(max_length=256)]] = None
    importExportFlag: Optional[Annotated[str, Field(pattern=r"^[12]$")]] = None
    confirmStatus: Optional[Annotated[str, Field(pattern=r"^[013]$")]] = None
    valuationMethod: Optional[Annotated[str, Field(max_length=128)]] = None
    prn: Optional[Annotated[str, Field(max_length=80)]] = None


class T108Response(BaseModel):
    sellerDetails: T108SellerDetails
    basicInformation: T108BasicInformation
    buyerDetails: T108BuyerDetails
    goodsDetails: List[T108GoodsItem]
    taxDetails: List[T108TaxDetail]
    summary: T108Summary
    payWay: Optional[List[T108PayWay]] = None
    extend: Optional[T108Extend] = None
    custom: Optional[T108Custom] = None


# =========================================================
# T109: BILLING UPLOAD (INVOICE/RECEIPT/DEBIT NOTE)
# =========================================================

class T109SellerDetails(BaseModel):
    tin: TIN
    ninBrn: Optional[NIN_BRN] = None
    legalName: Annotated[str, Field(max_length=256)]
    businessName: Optional[Annotated[str, Field(max_length=256)]] = None
    address: Optional[Annotated[str, Field(max_length=500)]] = None
    mobilePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    linePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    emailAddress: Annotated[str, Field(max_length=50)]  # Required, email format
    placeOfBusiness: Optional[Annotated[str, Field(max_length=500)]] = None
    referenceNo: Optional[CODE_50] = None
    
    @field_validator("emailAddress")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError("Invalid email format")
        return v


class T109BasicInformation(BaseModel):
    invoiceNo: Optional[CODE_20] = None  # Auto-generated if empty for online mode
    antifakeCode: Optional[CODE_20] = None
    deviceNo: DEVICE_NO
    issuedDate: DT_REQUEST  # yyyy-MM-dd HH:mm:ss
    operator: Annotated[str, Field(min_length=1, max_length=100)]
    currency: CURRENCY
    oriInvoiceId: Optional[CODE_20] = None
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    dataSource: DATA_SOURCE
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None
    isBatch: Optional[Annotated[str, Field(pattern=r"^[01]$")]] = "0"
    
    @model_validator(mode="after")
    def validate_mode_fields(self) -> "T109BasicInformation":
        # Offline mode (modeCode=0 in summary) requires these fields
        # This validation should be coordinated with summary.modeCode
        return self


class T109BuyerDetails(BaseModel):
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerPassportNum: Optional[CODE_20] = None
    buyerLegalName: Optional[Annotated[str, Field(max_length=256)]] = None
    buyerBusinessName: Optional[Annotated[str, Field(max_length=256)]] = None
    buyerAddress: Optional[Annotated[str, Field(max_length=500)]] = None
    buyerEmail: Optional[Annotated[str, Field(max_length=50)]] = None
    buyerMobilePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    buyerLinePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    buyerPlaceOfBusi: Optional[Annotated[str, Field(max_length=500)]] = None
    buyerType: BUYER_TYPE
    buyerCitizenship: Optional[Annotated[str, Field(max_length=128)]] = None
    buyerSector: Optional[Annotated[str, Field(max_length=200)]] = None
    buyerReferenceNo: Optional[CODE_50] = None
    
    @model_validator(mode="after")
    def validate_b2b_fields(self) -> "T109BuyerDetails":
        if self.buyerType in ["0", "3"]:  # B2B/B2G
            if not self.buyerTin:
                raise ValueError("buyerTin required for B2B/B2G transactions")
            if not self.buyerLegalName:
                raise ValueError("buyerLegalName required for B2B/B2G transactions")
        return self


class T109GoodsItem(BaseModel):
    item: Annotated[str, Field(min_length=1, max_length=100)]
    itemCode: CODE_50
    qty: Optional[AMOUNT_20_8] = None
    unitOfMeasure: CODE_3
    unitPrice: Optional[AMOUNT_20_8] = None
    total: AMOUNT_SIGNED_16_2
    taxRate: RATE_12_8
    tax: AMOUNT_SIGNED_16_2
    discountTotal: Optional[AMOUNT_SIGNED_16_2] = None
    discountTaxRate: Optional[RATE_12_8] = None
    orderNumber: Annotated[int, Field(ge=0)]
    discountFlag: DISCOUNT_FLAG
    deemedFlag: DEEMED_FLAG = "2"
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[Annotated[str, Field(max_length=1024)]] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: Annotated[str, Field(max_length=100)]
    exciseRate: Optional[Annotated[str, Field(max_length=21)]] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[Annotated[str, Field(max_length=100)]] = None
    
    @field_validator("item")
    @classmethod
    def validate_item_name(cls, v: str, info) -> str:
        # Item name logic based on discount/deemed flags
        # This is applied by the client before sending
        return v
    
    @model_validator(mode="after")
    def validate_item_amounts(self) -> "T109GoodsItem":
        if self.discountFlag == "0":  # Discount amount line
            if self.qty is not None or self.unitPrice is not None:
                raise ValueError("qty and unitPrice must be empty for discount amount lines")
            if self.total >= 0:
                raise ValueError("total must be negative for discount amount lines")
            if self.discountTotal is not None:
                raise ValueError("discountTotal must be empty for discount amount lines")
        elif self.discountFlag in ["1", "2"]:  # Normal or discount item
            if self.qty is None or self.unitPrice is None:
                raise ValueError("qty and unitPrice required for normal/discount items")
            if self.qty <= 0 or self.unitPrice <= 0:
                raise ValueError("qty and unitPrice must be positive")
            # Calculate expected total: qty * unitPrice, truncate to 2 decimals
            expected = (self.qty * self.unitPrice).quantize(Decimal("0.01"), rounding="ROUND_DOWN")
            if abs(self.total - expected) > Decimal("0.01"):
                raise ValueError(f"total mismatch: expected {expected}, got {self.total}")
        
        # Excise validation
        if self.exciseFlag == "1":
            if not self.categoryId or not self.exciseRate or not self.exciseRule:
                raise ValueError("categoryId, exciseRate, and exciseRule required for excise items")
            if self.exciseTax is None:
                raise ValueError("exciseTax required for excise items")
        
        return self


class T109TaxDetail(BaseModel):
    taxCategory: Annotated[str, Field(max_length=100)]
    netAmount: AMOUNT_16_2
    taxRate: RATE_12_8
    taxAmount: AMOUNT_16_2
    grossAmount: AMOUNT_16_2
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    taxRateName: Annotated[str, Field(max_length=100)]
    
    @model_validator(mode="after")
    def validate_tax_calculation(self) -> "T109TaxDetail":
        expected_gross = self.netAmount + self.taxAmount
        if abs(self.grossAmount - expected_gross) > Decimal("0.01"):
            raise ValueError(f"grossAmount mismatch: net({self.netAmount}) + tax({self.taxAmount}) = {expected_gross} ≠ {self.grossAmount}")
        return self


class T109Summary(BaseModel):
    netAmount: AMOUNT_16_2
    taxAmount: AMOUNT_16_2
    grossAmount: AMOUNT_16_2
    itemCount: Annotated[int, Field(ge=1)]
    modeCode: Annotated[str, Field(pattern=r"^[01]$")]  # 0=Offline, 1=Online
    remarks: Optional[Annotated[str, Field(max_length=500)]] = None
    qrCode: Optional[CODE_500] = None
    
    @model_validator(mode="after")
    def validate_summary_totals(self) -> "T109Summary":
        if self.grossAmount <= 0:
            raise ValueError("grossAmount must be positive")
        if self.modeCode == "0" and not self.qrCode:  # Offline mode requires QR
            raise ValueError("qrCode required for offline mode (modeCode=0)")
        return self


class T109PayWay(BaseModel):
    paymentMode: PAYMENT_MODE
    paymentAmount: AMOUNT_16_2
    orderNumber: Annotated[str, Field(min_length=1, max_length=10)]


class T109Extend(BaseModel):
    reason: Optional[Annotated[str, Field(max_length=1024)]] = None
    reasonCode: Optional[REASON_CODE] = None


class T109BillingUpload(BaseModel):
    sellerDetails: T109SellerDetails
    basicInformation: T109BasicInformation
    buyerDetails: Optional[T109BuyerDetails] = None
    goodsDetails: List[T109GoodsItem]
    taxDetails: List[T109TaxDetail]
    summary: T109Summary
    payWay: Optional[List[T109PayWay]] = None
    extend: Optional[T109Extend] = None
    
    @model_validator(mode="after")
    def validate_totals_match(self) -> "T109BillingUpload":
        # Validate goodsDetails totals match summary
        calc_net = sum(item.total - item.tax for item in self.goodsDetails if item.discountFlag != "0")
        calc_tax = sum(item.tax for item in self.goodsDetails if item.discountFlag != "0")
        calc_gross = sum(item.total for item in self.goodsDetails if item.discountFlag != "0")
        
        tolerance = Decimal("0.01")
        if abs(calc_net - self.summary.netAmount) > tolerance:
            raise ValueError(f"netAmount mismatch")
        if abs(calc_tax - self.summary.taxAmount) > tolerance:
            raise ValueError(f"taxAmount mismatch")
        if abs(calc_gross - self.summary.grossAmount) > tolerance:
            raise ValueError(f"grossAmount mismatch")
        
        # Validate itemCount
        item_count = sum(1 for item in self.goodsDetails if item.discountFlag != "0")
        if item_count != self.summary.itemCount:
            raise ValueError(f"itemCount mismatch: goodsDetails has {item_count} items, summary says {self.summary.itemCount}")
        
        return self


# =========================================================
# T110: CREDIT NOTE APPLICATION
# =========================================================

class T110GoodsItem(BaseModel):
    item: Annotated[str, Field(max_length=100)]
    itemCode: CODE_50
    qty: Annotated[Decimal, Field(le=0, max_digits=20, decimal_places=8)]  # Must be negative or zero
    unitOfMeasure: CODE_3
    unitPrice: AMOUNT_20_8
    total: Annotated[Decimal, Field(le=0, max_digits=16, decimal_places=2)]  # Must be negative or zero
    taxRate: RATE_12_8
    tax: Annotated[Decimal, Field(le=0, max_digits=16, decimal_places=2)]  # Must be negative or zero
    orderNumber: Annotated[int, Field(ge=0)]
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[Annotated[str, Field(max_length=1024)]] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: Annotated[str, Field(max_length=100)]
    exciseRate: Optional[Annotated[str, Field(max_length=21)]] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[Annotated[Decimal, Field(le=0, max_digits=16, decimal_places=2)]] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[Annotated[str, Field(max_length=100)]] = None


class T110TaxDetail(BaseModel):
    taxCategory: Annotated[str, Field(max_length=100)]
    netAmount: AMOUNT_16_2
    taxRate: RATE_12_8
    taxAmount: AMOUNT_16_2
    grossAmount: AMOUNT_16_2
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    taxRateName: Annotated[str, Field(max_length=100)]


class T110Summary(BaseModel):
    netAmount: Annotated[Decimal, Field(le=0, max_digits=16, decimal_places=2)]  # Negative for credit
    taxAmount: Annotated[Decimal, Field(le=0, max_digits=16, decimal_places=2)]
    grossAmount: Annotated[Decimal, Field(le=0, max_digits=16, decimal_places=2)]
    itemCount: Annotated[int, Field(ge=1)]
    modeCode: Annotated[str, Field(pattern=r"^[01]$")]
    qrCode: Optional[CODE_500] = None


class T110CreditApplication(BaseModel):
    oriInvoiceId: CODE_20
    oriInvoiceNo: CODE_20
    reasonCode: REASON_CODE
    reason: Optional[Annotated[str, Field(max_length=1024)]] = None
    applicationTime: DT_REQUEST
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[14]$")]  # 101=Credit, 104=Cancel Credit
    currency: CURRENCY
    contactName: Optional[Annotated[str, Field(max_length=200)]] = None
    contactMobileNum: Optional[Annotated[str, Field(max_length=30)]] = None
    contactEmail: Optional[Annotated[str, Field(max_length=50)]] = None
    source: DATA_SOURCE
    remarks: Optional[Annotated[str, Field(max_length=500)]] = None
    sellersReferenceNo: Optional[CODE_50] = None
    goodsDetails: List[T110GoodsItem]
    taxDetails: List[T110TaxDetail]
    summary: T110Summary
    payWay: Optional[List[T109PayWay]] = None
    
    @model_validator(mode="after")
    def validate_reason(self) -> "T110CreditApplication":
        if self.reasonCode == "105" and not self.reason:
            raise ValueError("reason required when reasonCode is 105 (Others)")
        return self
    
    @model_validator(mode="after")
    def validate_currency_match(self) -> "T110CreditApplication":
        # Currency must match original invoice - validated server-side
        return self


class T110Response(BaseModel):
    referenceNo: CODE_50


# =========================================================
# T111: CREDIT/DEBIT NOTE APPLICATION LIST QUERY
# =========================================================

class T111Request(BaseModel):
    referenceNo: Optional[CODE_20] = None
    oriInvoiceNo: Optional[CODE_20] = None
    invoiceNo: Optional[CODE_20] = None
    combineKeywords: Optional[Annotated[str, Field(max_length=20)]] = None
    approveStatus: Optional[APPROVE_STATUS] = None
    queryType: Annotated[str, Field(pattern=r"^[123]$")] = "1"  # 1=My apps, 2=To-approve, 3=Approved
    invoiceApplyCategoryCode: Optional[Annotated[str, Field(pattern=r"^10[134]$")]] = None
    startDate: Optional[DATE_ONLY] = None
    endDate: Optional[DATE_ONLY] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20


class T111Record(BaseModel):
    id: CODE_32
    oriInvoiceNo: CODE_20
    invoiceNo: Optional[CODE_20] = None
    referenceNo: CODE_50
    approveStatus: APPROVE_STATUS
    applicationTime: DT_RESPONSE
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[1-4]$")]
    grossAmount: AMOUNT_16_2
    oriGrossAmount: AMOUNT_16_2
    currency: CURRENCY
    taskId: CODE_20
    buyerTin: TIN
    buyerBusinessName: Annotated[str, Field(max_length=256)]
    buyerLegalName: Annotated[str, Field(max_length=256)]
    tin: TIN
    businessName: Annotated[str, Field(max_length=256)]
    legalName: Annotated[str, Field(max_length=256)]
    waitingDate: Annotated[int, Field(ge=0)]
    dataSource: DATA_SOURCE


class T111Response(BaseModel):
    page: T106Page
    records: List[T111Record]


# =========================================================
# T112/T118: CREDIT NOTE APPLICATION DETAILS
# =========================================================

class T112Request(BaseModel):
    id: CODE_20


class T112GoodsItem(BaseModel):
    itemName: Annotated[str, Field(max_length=60)]  # Note: API uses "itemName" here
    itemCode: CODE_50
    qty: AMOUNT_20_8
    unit: CODE_20  # Note: API uses "unit" not "unitOfMeasure"
    unitPrice: AMOUNT_20_8
    total: AMOUNT_SIGNED_16_2
    taxRate: RATE_12_8
    tax: AMOUNT_SIGNED_16_2
    discountTotal: Optional[AMOUNT_SIGNED_16_2] = None
    discountTaxRate: Optional[RATE_12_8] = None
    orderNumber: Annotated[int, Field(ge=0)]
    discountFlag: DISCOUNT_FLAG
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[Annotated[str, Field(max_length=1024)]] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: Annotated[str, Field(max_length=100)]
    exciseRate: Optional[Annotated[str, Field(max_length=21)]] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[Annotated[str, Field(max_length=100)]] = None


class T112Summary(BaseModel):
    netAmount: AMOUNT_SIGNED_16_2
    taxAmount: AMOUNT_SIGNED_16_2
    grossAmount: AMOUNT_SIGNED_16_2
    previousNetAmount: AMOUNT_16_2  # Original invoice values
    previousTaxAmount: AMOUNT_16_2
    previousGrossAmount: AMOUNT_16_2


class T112BasicInformation(BaseModel):
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None


class T112Response(BaseModel):
    id: CODE_20
    oriInvoiceNo: CODE_20
    oriInvoiceId: CODE_20
    refundInvoiceNo: Optional[CODE_20] = None
    referenceNo: CODE_50
    reason: Annotated[str, Field(max_length=1024)]
    selectRefundReasonCode: REASON_CODE
    approveStatusCode: APPROVE_STATUS
    updateTime: DT_RESPONSE
    applicationTime: DT_RESPONSE
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[1-4]$")]
    contactName: Optional[Annotated[str, Field(max_length=200)]] = None
    contactMobileNum: Optional[Annotated[str, Field(max_length=30)]] = None
    contactEmail: Optional[Annotated[str, Field(max_length=50)]] = None
    source: DATA_SOURCE
    taskId: Optional[CODE_20] = None
    remarks: Optional[Annotated[str, Field(max_length=500)]] = None
    grossAmount: AMOUNT_16_2
    totalAmount: AMOUNT_16_2
    currency: CURRENCY
    refundIssuedDate: Optional[DT_RESPONSE] = None
    issuedDate: DT_RESPONSE
    tin: TIN
    sellersReferenceNo: Optional[CODE_50] = None
    nin: NIN_BRN
    legalName: Annotated[str, Field(max_length=256)]
    businessName: Annotated[str, Field(max_length=256)]
    mobilePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    address: Optional[Annotated[str, Field(max_length=500)]] = None
    emailAddress: Optional[Annotated[str, Field(max_length=50)]] = None
    buyerTin: Optional[TIN] = None
    buyerNin: Optional[NIN_BRN] = None
    buyerLegalName: Optional[Annotated[str, Field(max_length=256)]] = None
    buyerBusinessName: Optional[Annotated[str, Field(max_length=256)]] = None
    buyerAddress: Optional[Annotated[str, Field(max_length=500)]] = None
    buyerEmailAddress: Optional[Annotated[str, Field(max_length=50)]] = None
    buyerMobilePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    buyerLinePhone: Optional[Annotated[str, Field(max_length=30)]] = None
    buyerCitizenship: Optional[Annotated[str, Field(max_length=128)]] = None
    buyerPassportNum: Optional[CODE_20] = None
    buyerPlaceOfBusi: Optional[Annotated[str, Field(max_length=500)]] = None
    goodsDetails: Optional[List[T112GoodsItem]] = None
    taxDetails: Optional[List[T108TaxDetail]] = None
    summary: Optional[T112Summary] = None
    payWay: Optional[List[T108PayWay]] = None
    basicInformation: Optional[T112BasicInformation] = None


# =========================================================
# T113: CREDIT NOTE APPROVAL
# =========================================================

class T113Request(BaseModel):
    referenceNo: CODE_20
    approveStatus: APPROVE_STATUS
    taskId: CODE_20
    remark: Annotated[str, Field(min_length=1, max_length=1024)]


# =========================================================
# T114: CANCEL CREDIT/DEBIT NOTE APPLICATION
# =========================================================

class T114Request(BaseModel):
    oriInvoiceId: CODE_20
    invoiceNo: CODE_20
    reason: Optional[Annotated[str, Field(max_length=1024)]] = None
    reasonCode: REASON_CODE
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[34]$")]  # 103=Cancel Debit, 104=Cancel Credit
    
    @model_validator(mode="after")
    def validate_reason(self) -> "T114Request":
        if self.reasonCode == "103" and not self.reason:
            raise ValueError("reason required when reasonCode is 103 (Other reasons)")
        return self


# =========================================================
# T115: SYSTEM DICTIONARY UPDATE
# =========================================================

class T115DictionaryValue(BaseModel):
    value: Annotated[str, Field(max_length=50)]
    name: Annotated[str, Field(max_length=100)]


class T115TaxCode(BaseModel):
    taxCode: CODE_20
    name: Annotated[str, Field(max_length=80)]
    rate: Annotated[str, Field(max_length=10)]  # "-1", "0", "0.18", etc.
    parentClass: CODE_20
    vatManagement: Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Zero, 102=Duty-free
    keyword: Annotated[str, Field(max_length=512)]
    goodService: Annotated[str, Field(max_length=80)]
    parentClass: CODE_80
    rateText: Annotated[str, Field(max_length=50)]


class T115ExciseDutyDetail(BaseModel):
    exciseDutyId: CODE_18
    type: Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Percentage, 102=Unit
    rate: Optional[Annotated[str, Field(max_length=21)]] = None
    unit: Optional[CODE_3] = None
    currency: Optional[CURRENCY] = None


class T115ExciseDuty(BaseModel):
    id: CODE_20
    exciseDutyCode: CODE_20
    goodService: Annotated[str, Field(max_length=500)]
    parentCode: CODE_20
    rateText: Annotated[str, Field(max_length=50)]
    isLeafNode: IS_LEAF_NODE
    effectiveDate: DT_RESPONSE
    exciseDutyDetailsList: List[T115ExciseDutyDetail]


class T115CommodityCategory(BaseModel):
    commodityCategoryCode: CODE_20
    parentCode: CODE_20
    commodityCategoryName: Annotated[str, Field(max_length=100)]
    commodityCategoryLevel: Annotated[int, Field(ge=1)]
    rate: RATE_12_8
    isLeafNode: IS_LEAF_NODE
    serviceMark: IS_LEAF_NODE
    isZeroRate: IS_LEAF_NODE
    zeroRateStartDate: Optional[DT_RESPONSE] = None
    zeroRateEndDate: Optional[DT_RESPONSE] = None
    isExempt: IS_LEAF_NODE
    exemptRateStartDate: Optional[DT_RESPONSE] = None
    exemptRateEndDate: Optional[DT_RESPONSE] = None
    enableStatusCode: ENABLE_STATUS
    exclusion: EXCLUSION_TYPE


class T115Format(BaseModel):
    dateFormat: Annotated[str, Field(pattern=r"^[dMy/]+$")]  # e.g., "dd/MM/yyyy"
    timeFormat: Annotated[str, Field(pattern=r"^[dMyHms/:]+$")]  # e.g., "dd/MM/yyyy HH:mm:ss"


class T115Response(BaseModel):
    creditNoteMaximumInvoicingDays: Optional[T115DictionaryValue] = None
    currencyType: Optional[List[T115DictionaryValue]] = None
    creditNoteValuePercentLimit: Optional[T115DictionaryValue] = None
    rateUnit: Optional[List[T115DictionaryValue]] = None
    format: Optional[T115Format] = None
    sector: Optional[List[Dict[str, str]]] = None
    payWay: Optional[List[T115DictionaryValue]] = None
    taxType: Optional[List[T115DictionaryValue]] = None
    countryCode: Optional[List[T115DictionaryValue]] = None
    taxCode: Optional[List[T115TaxCode]] = None
    exciseDutyList: Optional[List[T115ExciseDuty]] = None
    commodityCategoryList: Optional[List[T115CommodityCategory]] = None


# =========================================================
# T116: Z-REPORT DAILY UPLOAD (Placeholder - Spec TBD)
# =========================================================

class T116Request(BaseModel):
    # Fields to be determined per URA specification
    deviceNo: DEVICE_NO
    reportDate: DATE_ONLY
    # ... additional fields when spec is available
    model_config = ConfigDict(extra="allow")


# =========================================================
# T117: INVOICE CHECKS
# =========================================================

class T117InvoiceCheck(BaseModel):
    invoiceNo: CODE_20
    invoiceType: INVOICE_TYPE


class T117Request(RootModel[List[T117InvoiceCheck]]):
    pass

class T117Response(RootModel[List[T117InvoiceCheck]]):
    pass


# =========================================================
# T119: QUERY TAXPAYER BY TIN
# =========================================================

class T119Request(BaseModel):
    tin: Optional[TIN] = None
    ninBrn: Optional[NIN_BRN] = None
    
    @model_validator(mode="after")
    def require_identifier(self) -> "T119Request":
        if not self.tin and not self.ninBrn:
            raise ValueError("Either tin or ninBrn must be provided")
        return self


class T119TaxpayerInfo(BaseModel):
    tin: TIN
    ninBrn: NIN_BRN
    legalName: Annotated[str, Field(max_length=256)]
    businessName: Annotated[str, Field(max_length=256)]
    contactNumber: Annotated[str, Field(max_length=30)]
    contactEmail: Annotated[str, Field(max_length=50)]
    address: Annotated[str, Field(max_length=500)]


class T119Response(BaseModel):
    taxpayer: T119TaxpayerInfo


# =========================================================
# T120: VOID CREDIT/DEBIT NOTE APPLICATION
# =========================================================

class T120Request(BaseModel):
    businessKey: CODE_20
    referenceNo: CODE_20


# =========================================================
# T121: ACQUIRE EXCHANGE RATE (Single Currency)
# =========================================================

class T121Request(BaseModel):
    currency: CURRENCY


class T121Response(BaseModel):
    currency: CURRENCY
    rate: Annotated[str, Field(pattern=r"^\d+(\.\d+)?$")]  # e.g., "3700" for 1 USD = 3700 UGX


# =========================================================
# T122: QUERY INVALID CREDIT NOTE DETAILS
# =========================================================

class T122Request(BaseModel):
    invoiceNo: CODE_20


class T122Response(BaseModel):
    invoiceNo: CODE_20
    currency: CURRENCY
    issueDate: DT_RESPONSE
    grossAmount: AMOUNT_16_2
    reason: Annotated[str, Field(max_length=1024)]
    reasonCode: REASON_CODE


# =========================================================
# T123/T124/T134: COMMODITY CATEGORY QUERIES
# =========================================================

class T123CommodityCategory(BaseModel):
    commodityCategoryCode: CODE_20
    parentCode: CODE_20
    commodityCategoryName: Annotated[str, Field(max_length=100)]
    commodityCategoryLevel: Annotated[int, Field(ge=1)]
    rate: RATE_12_8
    isLeafNode: IS_LEAF_NODE
    serviceMark: IS_LEAF_NODE
    isZeroRate: IS_LEAF_NODE
    zeroRateStartDate: Optional[DT_RESPONSE] = None
    zeroRateEndDate: Optional[DT_RESPONSE] = None
    isExempt: IS_LEAF_NODE
    exemptRateStartDate: Optional[DT_RESPONSE] = None
    exemptRateEndDate: Optional[DT_RESPONSE] = None
    enableStatusCode: ENABLE_STATUS
    exclusion: EXCLUSION_TYPE


class T124Request(BaseModel):
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20


class T124Response(BaseModel):
    page: T106Page
    records: List[T123CommodityCategory]


class T134Request(BaseModel):
    commodityCategoryVersion: Annotated[str, Field(max_length=20)]  # Local version to compare


class T134Response(RootModel[List[T123CommodityCategory]]):
    pass
    


# =========================================================
# T125: QUERY EXCISE DUTY
# =========================================================

class T125ExciseDutyDetail(BaseModel):
    exciseDutyId: CODE_20
    type: Annotated[str, Field(pattern=r"^10[12]$")]
    rate: Optional[Annotated[str, Field(max_length=21)]] = None
    unit: Optional[CODE_3] = None
    currency: Optional[CURRENCY] = None


class T125ExciseDuty(BaseModel):
    id: CODE_20
    exciseDutyCode: CODE_20
    goodService: Annotated[str, Field(max_length=500)]
    parentCode: CODE_20
    rateText: Annotated[str, Field(max_length=50)]
    isLeafNode: IS_LEAF_NODE
    effectiveDate: DT_RESPONSE
    exciseDutyDetailsList: List[T125ExciseDutyDetail]


class T125Response(BaseModel):
    exciseDutyList: List[T125ExciseDuty]


# =========================================================
# T126: GET ALL EXCHANGE RATES
# =========================================================

class T126ExchangeRate(BaseModel):
    currency: CURRENCY
    rate: Annotated[str, Field(pattern=r"^\d+(\.\d+)?$")]


class T126Response(RootModel[List[T126ExchangeRate]]):
    pass


# =========================================================
# T127: GOODS/SERVICES INQUIRY
# =========================================================

class T127Request(BaseModel):
    goodsCode: Optional[CODE_50] = None
    goodsName: Optional[Annotated[str, Field(max_length=100)]] = None
    commodityCategoryName: Optional[Annotated[str, Field(max_length=200)]] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20


class T127GoodsRecord(BaseModel):
    id: CODE_20
    goodsName: Annotated[str, Field(max_length=100)]
    goodsCode: CODE_50
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    currency: CURRENCY
    stock: Annotated[int, Field(ge=0)]
    stockPrewarning: Annotated[int, Field(ge=0)]
    source: Annotated[str, Field(pattern=r"^10[12]$")]  # 101=URA, 102=Taxpayer
    statusCode: Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Enable, 102=Disable
    commodityCategoryCode: CODE_20
    commodityCategoryName: Annotated[str, Field(max_length=100)]
    taxRate: RATE_12_8
    isZeroRate: IS_LEAF_NODE
    isExempt: IS_LEAF_NODE
    haveExciseTax: HAVE_EXCISE
    exciseDutyCode: Optional[CODE_20] = None
    exciseDutyName: Optional[Annotated[str, Field(max_length=100)]] = None
    exciseRate: Optional[Annotated[str, Field(max_length=21)]] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    remarks: Optional[Annotated[str, Field(max_length=1024)]] = None
    packageScaledValue: Optional[AMOUNT_20_8] = None
    pieceScaledValue: Optional[AMOUNT_20_8] = None
    pieceMeasureUnit: Optional[CODE_3] = None
    havePieceUnit: HAVE_EXCISE
    pieceUnitPrice: Optional[AMOUNT_20_8] = None
    exclusion: EXCLUSION_TYPE


class T127Response(BaseModel):
    page: T106Page
    records: List[T127GoodsRecord]


# =========================================================
# T128: QUERY STOCK BY GOODS ID
# =========================================================

class T128Request(BaseModel):
    id: CODE_18


class T128Response(BaseModel):
    stock: Annotated[int, Field(ge=0)]
    stockPrewarning: Annotated[int, Field(ge=0)]


# =========================================================
# T129: BATCH INVOICE UPLOAD
# =========================================================

class T129InvoiceItem(BaseModel):
    invoiceContent: Annotated[str, Field(min_length=1)]  # T109 request JSON as string
    invoiceSignature: Annotated[str, Field(min_length=1)]  # Signature of invoiceContent


class T129Request(RootModel[List[T129InvoiceItem]]):
    pass


class T129ResultItem(BaseModel):
    invoiceContent: Annotated[str, Field(min_length=1)]  # T109 response JSON as string
    invoiceReturnCode: Annotated[str, Field(max_length=2)]  # "00"=Success, "99"=Error
    invoiceReturnMessage: Optional[Annotated[str, Field(max_length=500)]] = None


class T129Response(RootModel[List[T129ResultItem]]):
    pass


# =========================================================
# T130: GOODS UPLOAD
# =========================================================

class T130GoodsItem(BaseModel):
    goodsName: Annotated[str, Field(min_length=1, max_length=100)]
    goodsCode: Annotated[str, Field(min_length=1, max_length=50)]
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    currency: CURRENCY
    commodityCategoryId: CODE_18
    haveExciseTax: HAVE_EXCISE
    description: Optional[Annotated[str, Field(max_length=1024)]] = None
    stockPrewarning: Annotated[int, Field(ge=0)]
    pieceMeasureUnit: Optional[CODE_3] = None
    havePieceUnit: Optional[HAVE_EXCISE] = None
    pieceUnitPrice: Optional[AMOUNT_20_8] = None
    packageScaledValue: Optional[AMOUNT_20_8] = None
    pieceScaledValue: Optional[AMOUNT_20_8] = None
    exciseDutyCode: Optional[CODE_20] = None
    
    @model_validator(mode="after")
    def validate_excise_piece_logic(self) -> "T130GoodsItem":
        if self.haveExciseTax == "102":  # No excise
            if self.exciseDutyCode:
                raise ValueError("exciseDutyCode must be empty when haveExciseTax=102")
            if self.havePieceUnit == "101":
                raise ValueError("havePieceUnit must be 102 when haveExciseTax=102")
        
        if self.havePieceUnit == "102" or self.havePieceUnit is None:
            if self.pieceMeasureUnit or self.pieceUnitPrice or self.packageScaledValue or self.pieceScaledValue:
                raise ValueError("piece fields must be empty when havePieceUnit != 101")
        
        return self


class T130GoodsResult(BaseModel):
    goodsName: Annotated[str, Field(max_length=100)]
    goodsCode: CODE_50
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    currency: CURRENCY
    commodityCategoryId: CODE_18
    haveExciseTax: HAVE_EXCISE
    description: Optional[Annotated[str, Field(max_length=1024)]] = None
    stockPrewarning: Annotated[int, Field(ge=0)]
    pieceMeasureUnit: Optional[CODE_3] = None
    havePieceUnit: Optional[HAVE_EXCISE] = None
    pieceUnitPrice: Optional[AMOUNT_20_8] = None
    packageScaledValue: Optional[AMOUNT_20_8] = None
    pieceScaledValue: Optional[AMOUNT_20_8] = None
    exciseDutyCode: Optional[CODE_20] = None
    returnCode: Optional[Annotated[str, Field(max_length=4)]] = None  # Error code if failed
    returnMessage: Optional[Annotated[str, Field(max_length=500)]] = None


class T130Request(RootModel[List[T130GoodsItem]]):
    pass


class T130Response(RootModel[List[T130GoodsResult]]):
    pass


# =========================================================
# T131: GOODS STOCK MAINTAIN
# =========================================================

class T131StockItem(BaseModel):
    commodityGoodsId: CODE_20
    quantity: AMOUNT_20_8
    unitPrice: AMOUNT_20_8


class T131StockResult(BaseModel):
    commodityGoodsId: CODE_20
    quantity: AMOUNT_20_8
    unitPrice: AMOUNT_20_8
    returnCode: Optional[Annotated[str, Field(max_length=4)]] = None
    returnMessage: Optional[Annotated[str, Field(max_length=500)]] = None


class T131Request(BaseModel):
    operationType: OPERATION_TYPE
    stockInDate: DATE_ONLY
    stockInType: STOCK_IN_TYPE
    supplierTin: Optional[TIN] = None
    supplierName: Optional[Annotated[str, Field(max_length=200)]] = None
    remarks: Optional[Annotated[str, Field(max_length=200)]] = None
    goodsStockInItem: List[T131StockItem]


class T131Response(RootModel[List[T131StockResult]]):
    pass


# =========================================================
# T132: UPLOAD EXCEPTION LOG
# =========================================================

class T132ExceptionLog(BaseModel):
    interruptionTypeCode: Annotated[str, Field(pattern=r"^10[1-5]$")]  # 101-105 error types
    description: Annotated[str, Field(min_length=1, max_length=200)]
    errorDetail: Optional[Annotated[str, Field(max_length=4000)]] = None
    interruptionTime: DT_REQUEST


class T132Request(RootModel[List[T132ExceptionLog]]):
    pass


# =========================================================
# T137: CHECK TAXPAYER TYPE
# =========================================================

class T137Request(BaseModel):
    tin: TIN


class T137Response(BaseModel):
    taxpayerType: Annotated[str, Field(pattern=r"^[0123]$")]  # VAT status
    isExempt: YN
    isDeemed: YN


# =========================================================
# T138: GET REGISTERED BRANCHES
# =========================================================

class T138Request(BaseModel):
    tin: Optional[TIN] = None


class T138Branch(BaseModel):
    branchCode: CODE_10
    branchName: Annotated[str, Field(max_length=100)]
    branchType: CODE_3
    tin: TIN
    contactName: Annotated[str, Field(max_length=100)]
    contactEmail: Annotated[str, Field(max_length=50)]
    contactMobile: Annotated[str, Field(max_length=30)]
    contactNumber: Annotated[str, Field(max_length=30)]
    placeOfBusiness: Annotated[str, Field(max_length=500)]
    statusCode: ENABLE_STATUS


class T138Response(BaseModel):
    branches: List[T138Branch]


# =========================================================
# T139: STOCK TRANSFER BETWEEN BRANCHES
# =========================================================

class T139TransferItem(BaseModel):
    commodityGoodsId: CODE_20
    quantity: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=4)]
    unitPrice: AMOUNT_18_2
    fromBranch: CODE_10
    toBranch: CODE_10
    remarks: Optional[Annotated[str, Field(max_length=200)]] = None


class T139Request(BaseModel):
    transferDate: DATE_ONLY
    transferType: Annotated[str, Field(pattern=r"^10[12]$")]  # 101=Transfer Out, 102=Transfer In
    referenceNo: Optional[CODE_50] = None
    goodsTransferItem: List[T139TransferItem]


class T139Response(BaseModel):
    referenceNo: CODE_50


# =========================================================
# T144: QUERY GOODS BY CODE
# =========================================================

class T144Request(BaseModel):
    goodsCode: CODE_50
    tin: Optional[TIN] = None


class T144Response(BaseModel):
    id: CODE_20
    goodsName: Annotated[str, Field(max_length=100)]
    goodsCode: CODE_50
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    currency: CURRENCY
    stock: Annotated[int, Field(ge=0)]
    commodityCategoryCode: CODE_20
    commodityCategoryName: Annotated[str, Field(max_length=100)]
    taxRate: RATE_12_8
    haveExciseTax: HAVE_EXCISE
    exciseDutyCode: Optional[CODE_20] = None
    statusCode: ENABLE_STATUS


# =========================================================
# SCHEMA REGISTRY
# =========================================================

SCHEMAS: Dict[str, Any] = {
    # System
    "test_interface": T101Response,
    "client_init": T102Response,
    "sign_in": T103Response,
    "get_symmetric_key": T104Response,
    "forget_password": T105Request,
    
    # Invoice Management
    "invoice_query_all": T106Request,
    "invoice_query_normal": T107Request,
    "invoice_details": T108Request,
    "billing_upload": T109BillingUpload,
    "batch_invoice_upload": T129Request,
    
    # Credit/Debit Notes
    "credit_application": T110CreditApplication,
    "credit_note_query": T111Request,
    "credit_note_details": T112Request,
    "credit_note_approval": T113Request,
    "credit_note_cancel": T114Request,
    
    # Taxpayer/Branch
    "query_taxpayer": T119Request,
    "get_branches": T138Request,
    "check_taxpayer_type": T137Request,
    
    # Goods/Stock
    "query_commodity_category": None,  # T123 returns list directly
    "query_commodity_category_page": T124Request,
    "query_excise_duty": None,  # T125 returns object
    "get_exchange_rates": None,  # T126 returns list
    "get_exchange_rate": T121Request,
    "goods_inquiry": T127Request,
    "query_stock": T128Request,
    "goods_upload": T130Request,
    "stock_maintain": T131Request,
    "stock_transfer": T139Request,
    "query_goods_by_code": T144Request,
    
    # System/Utility
    "system_dictionary": None,  # T115 returns complex object
    "z_report_upload": T116Request,
    "invoice_checks": T117Request,
    "query_invalid_credit": T122Request,
    "commodity_incremental": T134Request,
    "exception_log_upload": T132Request,
    "void_application": T120Request,
}