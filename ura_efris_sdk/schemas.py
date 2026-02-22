from typing import List, Optional, Union, Literal, Dict, Any, Annotated
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, RootModel
from datetime import datetime
import re

# =========================================================
# CONFIGURATION
# =========================================================
class Config:
    arbitrary_types_allowed = True
    populate_by_name = True
    extra = 'ignore'  # Ignore extra fields from API responses

# =========================================================
# CUSTOM TYPES & VALIDATORS
# =========================================================

# --- Strings & Codes ---
TIN = Annotated[str, Field(min_length=10, max_length=20, pattern=r"^[A-Z0-9]{10,20}$")]
NIN_BRN = Annotated[str, Field(min_length=1, max_length=100)]
DEVICE_NO = Annotated[str, Field(min_length=1, max_length=20)]
UUID32 = Annotated[str, Field(min_length=32, max_length=32)]
CODE_1 = Annotated[str, Field(min_length=1, max_length=1)]
CODE_2 = Annotated[str, Field(min_length=1, max_length=2)]
CODE_3 = Annotated[str, Field(min_length=3, max_length=3)]
CODE_5 = Annotated[str, Field(min_length=1, max_length=5)]
CODE_6 = Annotated[str, Field(min_length=1, max_length=6)]
CODE_10 = Annotated[str, Field(min_length=1, max_length=10)]
CODE_16 = Annotated[str, Field(min_length=1, max_length=16)]
CODE_18 = Annotated[str, Field(min_length=1, max_length=18)]
CODE_20 = Annotated[str, Field(min_length=1, max_length=20)]
CODE_30 = Annotated[str, Field(min_length=1, max_length=30)]
CODE_32 = Annotated[str, Field(min_length=1, max_length=32)]
CODE_50 = Annotated[str, Field(min_length=1, max_length=50)]
CODE_80 = Annotated[str, Field(min_length=1, max_length=80)]
CODE_100 = Annotated[str, Field(min_length=1, max_length=100)]
CODE_128 = Annotated[str, Field(min_length=1, max_length=128)]
CODE_200 = Annotated[str, Field(min_length=1, max_length=200)]
CODE_256 = Annotated[str, Field(min_length=1, max_length=256)]
CODE_500 = Annotated[str, Field(min_length=1, max_length=500)]
CODE_1000 = Annotated[str, Field(min_length=1, max_length=1000)]
CODE_1024 = Annotated[str, Field(min_length=1, max_length=1024)]
CODE_4000 = Annotated[str, Field(min_length=1, max_length=4000)]

# --- Dates & Times ---
# Request: yyyy-MM-dd HH:mm:ss
DT_REQUEST = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")]
# Response: dd/MM/yyyy HH:mm:ss
DT_RESPONSE = Annotated[str, Field(pattern=r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$")]
# Date Only Request: yyyy-MM-dd
DATE_REQUEST = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
# Date Only Response: dd/MM/yyyy
DATE_RESPONSE = Annotated[str, Field(pattern=r"^\d{2}/\d{2}/\d{4}$")]

# --- Numbers & Amounts ---
# Amounts: Integer digits <= 16, Decimal digits <= 2 (Standard)
AMOUNT_16_2 = Annotated[Decimal, Field(max_digits=16, decimal_places=2)]
# Amounts: Integer digits <= 16, Decimal digits <= 4 (Tax/Net)
AMOUNT_16_4 = Annotated[Decimal, Field(max_digits=16, decimal_places=4)]
# Amounts: Integer digits <= 20, Decimal digits <= 8 (Quantity/UnitPrice)
AMOUNT_20_8 = Annotated[Decimal, Field(max_digits=20, decimal_places=8)]
# Signed Amounts (for Credit Notes/Discounts)
AMOUNT_SIGNED_16_2 = Annotated[Decimal, Field(max_digits=16, decimal_places=2)]
AMOUNT_SIGNED_16_4 = Annotated[Decimal, Field(max_digits=16, decimal_places=4)]
AMOUNT_SIGNED_20_8 = Annotated[Decimal, Field(max_digits=20, decimal_places=8)]

# Rates
RATE_12_8 = Annotated[Decimal, Field(max_digits=12, decimal_places=8)]
RATE_5_2 = Annotated[Decimal, Field(max_digits=5, decimal_places=2)]

# --- Enums & Flags ---
YN = Annotated[str, Field(pattern=r"^[YN]$")]
INVOICE_TYPE = Annotated[str, Field(pattern=r"^[1245]$")]  # 1:Invoice, 2:Credit, 4:Debit, 5:Credit Memo
INVOICE_KIND = Annotated[str, Field(pattern=r"^[12]$")]  # 1:Invoice, 2:Receipt
DATA_SOURCE = Annotated[str, Field(pattern=r"^10[1-8]$")]  # 101-108
INDUSTRY_CODE = Annotated[str, Field(pattern=r"^10[1-9]|11[0-2]$")]  # 101-112
DISCOUNT_FLAG = Annotated[str, Field(pattern=r"^[012]$")]  # 0:Discount Amount, 1:Discount Item, 2:Normal
DEEMED_FLAG = Annotated[str, Field(pattern=r"^[12]$")]  # 1:Deemed, 2:Not Deemed
EXCISE_FLAG = Annotated[str, Field(pattern=r"^[12]$")]  # 1:Excise, 2:Not Excise
EXCISE_RULE = Annotated[str, Field(pattern=r"^[12]$")]  # 1:Rate, 2:Quantity
BUYER_TYPE = Annotated[str, Field(pattern=r"^[0123]$")]  # 0:B2B, 1:B2C, 2:Foreigner, 3:B2G
APPROVE_STATUS = Annotated[str, Field(pattern=r"^10[1-4]$")]  # 101-104
REASON_CODE = Annotated[str, Field(pattern=r"^10[1-5]$")]
STOCK_LIMIT = Annotated[str, Field(pattern=r"^10[12]$")]  # 101:Restricted, 102:Unlimited
CURRENCY = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]
TAX_CATEGORY_CODE = Annotated[str, Field(pattern=r"^[0-9]{2}$")]  # 01-11
MODE_CODE = Annotated[str, Field(pattern=r"^[01]$")]  # 0:Offline, 1:Online
OPERATION_TYPE = Annotated[str, Field(pattern=r"^10[12]$")]  # 101:Stock In, 102:Stock Out
STOCK_IN_TYPE = Annotated[str, Field(pattern=r"^10[1-4]$")]  # 101-104
TRANSFER_TYPE = Annotated[str, Field(pattern=r"^10[1-3]$")]  # 101-103
QUERY_TYPE = Annotated[str, Field(pattern=r"^[01]$")]  # 0:Agent, 1:Normal
HAVE_EXCISE = Annotated[str, Field(pattern=r"^10[12]$")]  # 101:Yes, 102:No
HAVE_PIECE = Annotated[str, Field(pattern=r"^10[12]$")]
HAVE_CUSTOMS = Annotated[str, Field(pattern=r"^10[12]$")]
HAVE_OTHER = Annotated[str, Field(pattern=r"^10[12]$")]
SERVICE_MARK = Annotated[str, Field(pattern=r"^10[12]$")]
IS_LEAF_NODE = Annotated[str, Field(pattern=r"^10[12]$")]
ENABLE_STATUS = Annotated[str, Field(pattern=r"^[01]$")]
EXCLUSION_TYPE = Annotated[str, Field(pattern=r"^[0-3]$")]  # 0-3
VAT_APPLICABLE = Annotated[str, Field(pattern=r"^[01]$")]
DEEMED_EXEMPT_CODE = Annotated[str, Field(pattern=r"^10[12]$")]  # 101:Deemed, 102:Exempt
HIGH_SEA_BOND_FLAG = Annotated[str, Field(pattern=r"^[12]$")]  # 1:Yes, 2:No
DELIVERY_TERMS = Annotated[str, Field(max_length=3)]  # CIF, FOB, etc.

# =========================================================
# OUTER ENVELOPE (Protocol Format)
# =========================================================
class DataDescription(BaseModel):
    codeType: Annotated[str, Field(pattern=r"^[01]$")]  # 0:Plain, 1:Cipher
    encryptCode: Annotated[str, Field(pattern=r"^[12]$")]  # 1:RSA, 2:AES
    zipCode: Annotated[str, Field(pattern=r"^[01]$")]  # 0:Uncompressed, 1:Compressed

class Data(BaseModel):
    content: Optional[Annotated[str, Field(max_length=40000)]] = None  # Base64 Encoded JSON
    signature: Optional[Annotated[str, Field(max_length=500)]] = None
    dataDescription: DataDescription

class ExtendField(BaseModel):
    responseDateFormat: Optional[Annotated[str, Field(max_length=20)]] = "dd/MM/yyyy"
    responseTimeFormat: Optional[Annotated[str, Field(max_length=20)]] = "dd/MM/yyyy HH:mm:ss"
    referenceNo: Optional[CODE_50] = None
    operatorName: Optional[CODE_150] = None
    itemDescription: Optional[CODE_100] = None
    currency: Optional[CURRENCY] = None
    grossAmount: Optional[str] = None
    taxAmount: Optional[str] = None
    offlineInvoiceException: Optional[Dict[str, str]] = None

CODE_150 = Annotated[str, Field(min_length=1, max_length=150)]

class GlobalInfo(BaseModel):
    appId: Annotated[str, Field(max_length=5)]  # AP04, AP05
    version: Annotated[str, Field(max_length=15)]
    dataExchangeId: UUID32
    interfaceCode: Annotated[str, Field(max_length=5)]  # T101, T109, etc.
    requestCode: Annotated[str, Field(max_length=5)]  # TP
    requestTime: DT_REQUEST
    responseCode: Annotated[str, Field(max_length=5)]  # TA
    userName: Annotated[str, Field(max_length=20)]
    deviceMAC: Annotated[str, Field(max_length=25)]
    deviceNo: DEVICE_NO
    tin: TIN
    brn: Optional[NIN_BRN] = None
    taxpayerID: Annotated[str, Field(max_length=20)]
    longitude: Optional[Annotated[str, Field(max_length=60)]] = None
    latitude: Optional[Annotated[str, Field(max_length=60)]] = None
    agentType: Optional[Annotated[str, Field(max_length=1)]] = "0"
    extendField: Optional[ExtendField] = None

class ReturnStateInfo(BaseModel):
    returnCode: Annotated[str, Field(max_length=4)]
    returnMessage: Optional[Annotated[str, Field(max_length=500)]] = None

class ApiEnvelope(BaseModel):
    data: Data
    globalInfo: GlobalInfo
    returnStateInfo: ReturnStateInfo

# =========================================================
# T101: GET SERVER TIME
# =========================================================
class T101Response(BaseModel):
    currentTime: DT_RESPONSE

# =========================================================
# T102: CLIENT INITIALIZATION
# =========================================================
class T102Request(BaseModel):
    otp: Optional[Annotated[str, Field(max_length=6)]] = None

class T102Response(BaseModel):
    clientPriKey: Annotated[str, Field(max_length=4000)]
    serverPubKey: Annotated[str, Field(max_length=4000)]
    keyTable: Annotated[str, Field(max_length=4000)]

# =========================================================
# T103: SIGN IN / LOGIN
# =========================================================
class T103Device(BaseModel):
    deviceModel: CODE_50
    deviceNo: DEVICE_NO
    deviceStatus: CODE_3
    deviceType: CODE_3
    validPeriod: DATE_RESPONSE
    offlineAmount: str
    offlineDays: str
    offlineValue: str

class T103Taxpayer(BaseModel):
    id: CODE_18
    tin: TIN
    ninBrn: NIN_BRN
    legalName: CODE_256
    businessName: CODE_256
    taxpayerStatusId: CODE_3
    taxpayerRegistrationStatusId: CODE_3
    taxpayerType: CODE_3
    businessType: CODE_3
    departmentId: CODE_6
    contactName: CODE_100
    contactEmail: CODE_50
    contactMobile: CODE_30
    contactNumber: CODE_30
    placeOfBusiness: CODE_500

class T103TaxpayerBranch(BaseModel):
    branchCode: CODE_10
    branchName: CODE_500
    branchType: CODE_3
    contactName: CODE_100
    contactEmail: CODE_50
    contactMobile: CODE_30
    contactNumber: CODE_30
    placeOfBusiness: CODE_1000

class T103TaxType(BaseModel):
    taxTypeName: CODE_200
    taxTypeCode: CODE_3
    registrationDate: DATE_RESPONSE
    cancellationDate: Optional[DATE_RESPONSE] = None

class T103Response(BaseModel):
    device: T103Device
    taxpayer: T103Taxpayer
    taxpayerBranch: Optional[T103TaxpayerBranch] = None
    taxType: List[T103TaxType]
    dictionaryVersion: str
    issueTaxTypeRestrictions: Annotated[str, Field(pattern=r"^[01]$")]
    taxpayerBranchVersion: CODE_20
    commodityCategoryVersion: CODE_10
    exciseDutyVersion: CODE_10
    sellersLogo: Optional[str] = None  # Base64
    whetherEnableServerStock: Annotated[str, Field(pattern=r"^[01]$")]
    goodsStockLimit: STOCK_LIMIT
    exportCommodityTaxRate: str
    exportInvoiceExciseDuty: Annotated[str, Field(pattern=r"^[01]$")]
    maxGrossAmount: str
    isAllowBackDate: Annotated[str, Field(pattern=r"^[01]$")]
    isReferenceNumberMandatory: Annotated[str, Field(pattern=r"^[01]$")]
    isAllowIssueRebate: Annotated[str, Field(pattern=r"^[01]$")]
    isDutyFreeTaxpayer: Annotated[str, Field(pattern=r"^[01]$")]
    isAllowIssueCreditWithoutFDN: Annotated[str, Field(pattern=r"^[01]$")]
    periodDate: str
    isTaxCategoryCodeMandatory: Annotated[str, Field(pattern=r"^[01]$")]
    isAllowIssueInvoice: Annotated[str, Field(pattern=r"^[01]$")]
    isAllowOutOfScopeVAT: Annotated[str, Field(pattern=r"^[01]$")]
    creditMemoPeriodDate: str
    commGoodsLatestModifyVersion: CODE_14
    financialYearDate: CODE_4
    buyerModifiedTimes: str
    buyerModificationPeriod: str
    agentFlag: Annotated[str, Field(pattern=r"^[01]$")]
    webServiceURL: str
    environment: Annotated[str, Field(pattern=r"^[01]$")]
    frequentContactsLimit: str
    autoCalculateSectionE: Annotated[str, Field(pattern=r"^[01]$")]
    autoCalculateSectionF: Annotated[str, Field(pattern=r"^[01]$")]
    hsCodeVersion: str
    issueDebitNote: Annotated[str, Field(pattern=r"^[01]$")]
    qrCodeURL: str

CODE_14 = Annotated[str, Field(min_length=1, max_length=14)]
CODE_4 = Annotated[str, Field(min_length=1, max_length=4)]

# =========================================================
# T104: GET SYMMETRIC KEY
# =========================================================
class T104Response(BaseModel):
    passowrdDes: str  # Typo in API spec
    sign: str

# =========================================================
# T105: FORGET PASSWORD
# =========================================================
class T105Request(BaseModel):
    userName: CODE_200
    changedPassword: CODE_200

# =========================================================
# T106: INVOICE/RECEIPT QUERY
# =========================================================
class T106Request(BaseModel):
    oriInvoiceNo: Optional[CODE_20] = None
    invoiceNo: Optional[CODE_20] = None
    deviceNo: Optional[DEVICE_NO] = None
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerLegalName: Optional[CODE_256] = None
    combineKeywords: Optional[CODE_20] = None
    invoiceType: Optional[INVOICE_TYPE] = None
    invoiceKind: Optional[INVOICE_KIND] = None
    isInvalid: Optional[YN] = None
    isRefund: Optional[Annotated[str, Field(pattern=r"^[012]$")]] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20
    referenceNo: Optional[CODE_50] = None
    branchName: Optional[CODE_500] = None
    queryType: Optional[QUERY_TYPE] = "1"
    dataSource: Optional[DATA_SOURCE] = None
    sellerTinOrNin: Optional[CODE_100] = None
    sellerLegalOrBusinessName: Optional[CODE_256] = None

class T106Record(BaseModel):
    id: CODE_32
    invoiceNo: CODE_30
    oriInvoiceId: CODE_32
    oriInvoiceNo: CODE_30
    issuedDate: DT_RESPONSE
    buyerTin: Optional[TIN] = None
    buyerLegalName: Optional[CODE_256] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    currency: CURRENCY
    grossAmount: str
    taxAmount: str
    dataSource: DATA_SOURCE
    isInvalid: Optional[YN] = None
    isRefund: Optional[Annotated[str, Field(pattern=r"^[012]$")]] = None
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None
    branchName: CODE_500
    deviceNo: DEVICE_NO
    uploadingTime: DT_RESPONSE
    referenceNo: Optional[CODE_50] = None
    operator: CODE_100
    userName: CODE_500

class T106Page(BaseModel):
    pageNo: int
    pageSize: int
    totalSize: int
    pageCount: int

class T106Response(BaseModel):
    page: T106Page
    records: List[T106Record]

# =========================================================
# T107: QUERY NORMAL INVOICE/RECEIPT
# =========================================================
class T107Request(BaseModel):
    invoiceNo: Optional[CODE_20] = None
    deviceNo: Optional[DEVICE_NO] = None
    buyerTin: Optional[TIN] = None
    buyerLegalName: Optional[CODE_20] = None
    invoiceType: Optional[Annotated[str, Field(pattern=r"^[14]$")]] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20
    branchName: Optional[CODE_500] = None

class T107Record(BaseModel):
    id: CODE_32
    invoiceNo: CODE_20
    oriInvoiceId: CODE_32
    oriInvoiceNo: CODE_20
    issuedDate: DT_RESPONSE
    buyerTin: TIN
    buyerBusinessName: CODE_256
    buyerLegalName: CODE_256
    tin: TIN
    businessName: CODE_256
    legalName: CODE_256
    currency: CURRENCY
    grossAmount: str
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
    legalName: CODE_256
    businessName: CODE_256
    address: Optional[CODE_500] = None
    mobilePhone: Optional[CODE_30] = None
    linePhone: Optional[CODE_30] = None
    emailAddress: Optional[CODE_50] = None
    placeOfBusiness: Optional[CODE_500] = None
    referenceNo: Optional[CODE_50] = None
    branchId: CODE_18
    branchName: CODE_500
    branchCode: CODE_50

class T108BasicInformation(BaseModel):
    invoiceId: CODE_32
    invoiceNo: CODE_20
    oriInvoiceNo: Optional[CODE_20] = None
    antifakeCode: Optional[CODE_20] = None
    deviceNo: DEVICE_NO
    issuedDate: DT_RESPONSE
    oriIssuedDate: Optional[DT_RESPONSE] = None
    oriGrossAmount: Optional[str] = None
    operator: CODE_150
    currency: CURRENCY
    oriInvoiceId: Optional[CODE_32] = None
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    dataSource: DATA_SOURCE
    isInvalid: Optional[YN] = None
    isRefund: Optional[Annotated[str, Field(pattern=r"^[012]$")]] = None
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None
    currencyRate: Optional[str] = None

class T108BuyerDetails(BaseModel):
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerPassportNum: Optional[CODE_20] = None
    buyerLegalName: Optional[CODE_256] = None
    buyerBusinessName: Optional[CODE_256] = None
    buyerAddress: Optional[CODE_500] = None
    buyerEmail: Optional[CODE_50] = None
    buyerMobilePhone: Optional[CODE_30] = None
    buyerLinePhone: Optional[CODE_30] = None
    buyerPlaceOfBusi: Optional[CODE_500] = None
    buyerType: BUYER_TYPE
    buyerCitizenship: Optional[CODE_128] = None
    buyerSector: Optional[CODE_200] = None
    buyerReferenceNo: Optional[CODE_50] = None
    deliveryTermsCode: Optional[DELIVERY_TERMS] = None

class T108BuyerExtend(BaseModel):
    propertyType: Optional[CODE_50] = None
    district: Optional[CODE_50] = None
    municipalityCounty: Optional[CODE_50] = None
    divisionSubcounty: Optional[CODE_50] = None
    town: Optional[CODE_50] = None
    cellVillage: Optional[CODE_60] = None
    effectiveRegistrationDate: Optional[DATE_REQUEST] = None
    meterStatus: Optional[CODE_3] = None

CODE_60 = Annotated[str, Field(min_length=1, max_length=60)]

class T108GoodsItem(BaseModel):
    invoiceItemId: CODE_18
    item: CODE_200
    itemCode: CODE_50
    qty: Optional[AMOUNT_20_8] = None
    unitOfMeasure: CODE_3
    unitPrice: Optional[AMOUNT_20_8] = None
    total: AMOUNT_SIGNED_16_2
    taxRate: RATE_12_8
    tax: AMOUNT_SIGNED_16_2
    discountTotal: Optional[AMOUNT_SIGNED_16_2] = None
    discountTaxRate: Optional[RATE_12_8] = None
    orderNumber: int
    discountFlag: DISCOUNT_FLAG
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[CODE_1024] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: CODE_200
    exciseRate: Optional[CODE_21] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[CODE_100] = None
    vatApplicableFlag: Optional[VAT_APPLICABLE] = "1"
    deemedExemptCode: Optional[DEEMED_EXEMPT_CODE] = None
    vatProjectId: Optional[CODE_18] = None
    vatProjectName: Optional[CODE_100] = None
    totalWeight: Optional[str] = None
    hsCode: Optional[CODE_50] = None
    hsName: Optional[CODE_1000] = None
    pieceQty: Optional[AMOUNT_20_8] = None
    pieceMeasureUnit: Optional[CODE_3] = None
    highSeaBondFlag: Optional[HIGH_SEA_BOND_FLAG] = None
    highSeaBondCode: Optional[CODE_3] = None
    highSeaBondNo: Optional[CODE_50] = None

CODE_21 = Annotated[str, Field(min_length=1, max_length=21)]
CODE_1024 = Annotated[str, Field(min_length=1, max_length=1024)]

class T108TaxDetail(BaseModel):
    taxCategoryCode: TAX_CATEGORY_CODE
    netAmount: AMOUNT_16_4
    taxRate: RATE_12_8
    taxAmount: AMOUNT_16_4
    grossAmount: AMOUNT_16_4
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    taxRateName: Optional[CODE_100] = None

class T108Summary(BaseModel):
    netAmount: str
    taxAmount: str
    grossAmount: str
    itemCount: Annotated[int, Field(ge=1)]
    modeCode: MODE_CODE
    remarks: Optional[CODE_500] = None
    qrCode: Optional[CODE_500] = None

class T108PayWay(BaseModel):
    paymentMode: CODE_3
    paymentAmount: AMOUNT_16_2
    orderNumber: str

class T108Extend(BaseModel):
    reason: Optional[CODE_1024] = None
    reasonCode: Optional[REASON_CODE] = None

class T108Custom(BaseModel):
    sadNumber: Optional[CODE_20] = None
    office: Optional[CODE_35] = None
    cif: Optional[CODE_50] = None
    wareHouseNumber: Optional[CODE_16] = None
    wareHouseName: Optional[CODE_256] = None
    destinationCountry: Optional[CODE_256] = None
    originCountry: Optional[CODE_256] = None
    importExportFlag: Optional[Annotated[str, Field(pattern=r"^[12]$")]] = None
    confirmStatus: Optional[Annotated[str, Field(pattern=r"^[012]$")]] = None
    valuationMethod: Optional[CODE_128] = None
    prn: Optional[CODE_80] = None
    exportRegime: Optional[CODE_50] = None  # V23.7 Update

CODE_35 = Annotated[str, Field(min_length=1, max_length=35)]

class T108ImportServicesSeller(BaseModel):
    importBusinessName: Optional[CODE_500] = None
    importEmailAddress: Optional[CODE_50] = None
    importContactNumber: Optional[CODE_30] = None
    importAddress: Optional[CODE_500] = None
    importInvoiceDate: Optional[DATE_REQUEST] = None
    importAttachmentName: Optional[CODE_256] = None
    importAttachmentContent: Optional[str] = None

class T108AirlineGoodsDetails(BaseModel):
    item: CODE_200
    itemCode: Optional[CODE_50] = None
    qty: AMOUNT_20_8
    unitOfMeasure: CODE_3
    unitPrice: AMOUNT_20_8
    total: AMOUNT_SIGNED_16_2
    taxRate: Optional[RATE_12_8] = None
    tax: Optional[AMOUNT_SIGNED_16_2] = None
    discountTotal: Optional[AMOUNT_SIGNED_16_2] = None
    discountTaxRate: Optional[RATE_12_8] = None
    orderNumber: int
    discountFlag: DISCOUNT_FLAG
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[CODE_1024] = None
    goodsCategoryId: Optional[CODE_18] = None
    goodsCategoryName: Optional[CODE_200] = None
    exciseRate: Optional[CODE_21] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[CODE_100] = None

class T108EdcDetails(BaseModel):
    tankNo: Optional[CODE_50] = None
    pumpNo: Optional[CODE_50] = None
    nozzleNo: Optional[CODE_50] = None
    controllerNo: Optional[CODE_50] = None
    acquisitionEquipmentNo: Optional[CODE_50] = None
    levelGaugeNo: Optional[CODE_50] = None
    mvrn: Optional[CODE_32] = None
    updateTimes: Optional[str] = None

class T108AgentEntity(BaseModel):
    tin: Optional[TIN] = None
    legalName: Optional[CODE_256] = None
    businessName: Optional[CODE_256] = None
    address: Optional[CODE_500] = None

class T108CreditNoteExtend(BaseModel):
    preGrossAmount: Optional[str] = None
    preTaxAmount: Optional[str] = None
    preNetAmount: Optional[str] = None

class T108Response(BaseModel):
    sellerDetails: T108SellerDetails
    basicInformation: T108BasicInformation
    buyerDetails: T108BuyerDetails
    buyerExtend: Optional[T108BuyerExtend] = None
    goodsDetails: List[T108GoodsItem]
    taxDetails: List[T108TaxDetail]
    summary: T108Summary
    payWay: Optional[List[T108PayWay]] = None
    extend: Optional[T108Extend] = None
    custom: Optional[T108Custom] = None
    importServicesSeller: Optional[T108ImportServicesSeller] = None
    airlineGoodsDetails: Optional[List[T108AirlineGoodsDetails]] = None
    edcDetails: Optional[T108EdcDetails] = None
    agentEntity: Optional[T108AgentEntity] = None
    creditNoteExtend: Optional[T108CreditNoteExtend] = None
    existInvoiceList: Optional[List[Dict[str, str]]] = None

# =========================================================
# T109: INVOICE UPLOAD (BILLING)
# =========================================================
# Reuses most structures from T108 but with Request-specific validation
class T109SellerDetails(BaseModel):
    tin: TIN
    ninBrn: Optional[NIN_BRN] = None
    legalName: CODE_256
    businessName: Optional[CODE_256] = None
    address: Optional[CODE_500] = None
    mobilePhone: Optional[CODE_30] = None
    linePhone: Optional[CODE_30] = None
    emailAddress: CODE_50
    placeOfBusiness: Optional[CODE_500] = None
    referenceNo: Optional[CODE_50] = None
    branchId: Optional[CODE_18] = None
    isCheckReferenceNo: Optional[Annotated[str, Field(pattern=r"^[01]$")]] = "0"

class T109BasicInformation(BaseModel):
    invoiceNo: Optional[CODE_20] = None
    antifakeCode: Optional[CODE_20] = None
    deviceNo: DEVICE_NO
    issuedDate: DT_REQUEST
    operator: CODE_150
    currency: CURRENCY
    oriInvoiceId: Optional[CODE_20] = None
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    dataSource: DATA_SOURCE
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None
    isBatch: Optional[Annotated[str, Field(pattern=r"^[01]$")]] = "0"

class T109BuyerDetails(BaseModel):
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerPassportNum: Optional[CODE_20] = None
    buyerLegalName: Optional[CODE_256] = None
    buyerBusinessName: Optional[CODE_256] = None
    buyerAddress: Optional[CODE_500] = None
    buyerEmail: Optional[CODE_50] = None
    buyerMobilePhone: Optional[CODE_30] = None
    buyerLinePhone: Optional[CODE_30] = None
    buyerPlaceOfBusi: Optional[CODE_500] = None
    buyerType: BUYER_TYPE
    buyerCitizenship: Optional[CODE_128] = None
    buyerSector: Optional[CODE_200] = None
    buyerReferenceNo: Optional[CODE_50] = None
    nonResidentFlag: Optional[Annotated[str, Field(pattern=r"^[01]$")]] = "0"
    deliveryTermsCode: Optional[DELIVERY_TERMS] = None

class T109GoodsItem(BaseModel):
    item: CODE_200
    itemCode: CODE_50
    qty: Optional[AMOUNT_20_8] = None
    unitOfMeasure: CODE_3
    unitPrice: Optional[AMOUNT_20_8] = None
    total: AMOUNT_SIGNED_16_2
    taxRate: RATE_12_8
    tax: AMOUNT_SIGNED_16_2
    discountTotal: Optional[AMOUNT_SIGNED_16_2] = None
    discountTaxRate: Optional[RATE_12_8] = None
    orderNumber: int
    discountFlag: DISCOUNT_FLAG
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[CODE_1024] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: CODE_200
    exciseRate: Optional[CODE_21] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[CODE_100] = None
    vatApplicableFlag: Optional[VAT_APPLICABLE] = "1"
    deemedExemptCode: Optional[DEEMED_EXEMPT_CODE] = None
    vatProjectId: Optional[CODE_18] = None
    vatProjectName: Optional[CODE_100] = None
    hsCode: Optional[CODE_50] = None
    hsName: Optional[CODE_1000] = None
    totalWeight: Optional[str] = None
    pieceQty: Optional[AMOUNT_20_8] = None
    pieceMeasureUnit: Optional[CODE_3] = None
    highSeaBondFlag: Optional[HIGH_SEA_BOND_FLAG] = None
    highSeaBondCode: Optional[CODE_3] = None
    highSeaBondNo: Optional[CODE_50] = None

class T109TaxDetail(BaseModel):
    taxCategoryCode: TAX_CATEGORY_CODE
    netAmount: AMOUNT_16_4
    taxRate: RATE_12_8
    taxAmount: AMOUNT_16_4
    grossAmount: AMOUNT_16_4
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    taxRateName: Optional[CODE_100] = None

class T109Summary(BaseModel):
    netAmount: str
    taxAmount: str
    grossAmount: str
    itemCount: Annotated[int, Field(ge=1)]
    modeCode: MODE_CODE
    remarks: Optional[CODE_500] = None
    qrCode: Optional[CODE_500] = None

class T109PayWay(BaseModel):
    paymentMode: CODE_3
    paymentAmount: AMOUNT_16_2
    orderNumber: str

class T109Extend(BaseModel):
    reason: Optional[CODE_1024] = None
    reasonCode: Optional[REASON_CODE] = None

class T109BillingUpload(BaseModel):
    sellerDetails: T109SellerDetails
    basicInformation: T109BasicInformation
    buyerDetails: Optional[T109BuyerDetails] = None
    buyerExtend: Optional[T108BuyerExtend] = None
    goodsDetails: List[T109GoodsItem]
    taxDetails: List[T109TaxDetail]
    summary: T109Summary
    payWay: Optional[List[T109PayWay]] = None
    extend: Optional[T109Extend] = None
    importServicesSeller: Optional[T108ImportServicesSeller] = None
    airlineGoodsDetails: Optional[List[T108AirlineGoodsDetails]] = None
    edcDetails: Optional[T108EdcDetails] = None

class T109Response(BaseModel):
    # Returns similar structure to T108Response with added existInvoiceList
    sellerDetails: T108SellerDetails
    basicInformation: T108BasicInformation
    buyerDetails: T108BuyerDetails
    goodsDetails: List[T108GoodsItem]
    taxDetails: List[T108TaxDetail]
    summary: T108Summary
    payWay: Optional[List[T108PayWay]] = None
    extend: Optional[T108Extend] = None
    importServicesSeller: Optional[T108ImportServicesSeller] = None
    airlineGoodsDetails: Optional[List[T108AirlineGoodsDetails]] = None
    edcDetails: Optional[T108EdcDetails] = None
    existInvoiceList: Optional[List[Dict[str, str]]] = None
    agentEntity: Optional[T108AgentEntity] = None

# =========================================================
# T110: CREDIT NOTE APPLICATION
# =========================================================
class T110GoodsItem(BaseModel):
    item: CODE_200
    itemCode: CODE_50
    qty: AMOUNT_SIGNED_20_8  # Must be negative
    unitOfMeasure: CODE_3
    unitPrice: AMOUNT_20_8
    total: AMOUNT_SIGNED_16_2  # Must be negative
    taxRate: RATE_12_8
    tax: AMOUNT_SIGNED_16_2  # Must be negative
    orderNumber: int
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[CODE_1024] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: CODE_200
    exciseRate: Optional[CODE_21] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[CODE_100] = None
    vatApplicableFlag: Optional[VAT_APPLICABLE] = "1"

class T110TaxDetail(BaseModel):
    taxCategoryCode: TAX_CATEGORY_CODE
    netAmount: AMOUNT_SIGNED_16_4  # Negative
    taxRate: RATE_12_8
    taxAmount: AMOUNT_SIGNED_16_4  # Negative
    grossAmount: AMOUNT_SIGNED_16_4  # Negative
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    taxRateName: Optional[CODE_100] = None

class T110Summary(BaseModel):
    netAmount: AMOUNT_SIGNED_16_2
    taxAmount: AMOUNT_SIGNED_16_2
    grossAmount: AMOUNT_SIGNED_16_2
    itemCount: Annotated[int, Field(ge=1)]
    modeCode: MODE_CODE
    qrCode: Optional[CODE_500] = None

class T110Attachment(BaseModel):
    fileName: CODE_256
    fileType: CODE_5
    fileContent: str  # Base64

class T110CreditApplication(BaseModel):
    oriInvoiceId: CODE_20
    oriInvoiceNo: CODE_20
    reasonCode: REASON_CODE
    reason: Optional[CODE_1024] = None
    applicationTime: DT_REQUEST
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[14]$")]
    currency: CURRENCY
    contactName: Optional[CODE_200] = None
    contactMobileNum: Optional[CODE_30] = None
    contactEmail: Optional[CODE_50] = None
    source: DATA_SOURCE
    remarks: Optional[CODE_500] = None
    sellersReferenceNo: Optional[CODE_50] = None
    goodsDetails: List[T110GoodsItem]
    taxDetails: List[T110TaxDetail]
    summary: T110Summary
    payWay: Optional[List[T109PayWay]] = None
    buyerDetails: Optional[T109BuyerDetails] = None
    importServicesSeller: Optional[T108ImportServicesSeller] = None
    basicInformation: Optional[T109BasicInformation] = None
    attachmentList: Optional[List[T110Attachment]] = None

class T110Response(BaseModel):
    referenceNo: CODE_50

# =========================================================
# T111: CREDIT/DEBIT NOTE APPLICATION LIST QUERY
# =========================================================
class T111Request(BaseModel):
    referenceNo: Optional[CODE_20] = None
    oriInvoiceNo: Optional[CODE_20] = None
    invoiceNo: Optional[CODE_20] = None
    combineKeywords: Optional[CODE_20] = None
    approveStatus: Optional[APPROVE_STATUS] = None
    queryType: Annotated[str, Field(pattern=r"^[123]$")] = "1"
    invoiceApplyCategoryCode: Optional[Annotated[str, Field(pattern=r"^10[134]$")]] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20
    creditNoteType: Optional[Annotated[str, Field(pattern=r"^[12]$")]] = None
    branchName: Optional[CODE_500] = None
    sellerTinOrNin: Optional[CODE_100] = None
    sellerLegalOrBusinessName: Optional[CODE_256] = None

class T111Record(BaseModel):
    id: CODE_18
    oriInvoiceNo: CODE_20
    invoiceNo: Optional[CODE_20] = None
    referenceNo: CODE_20
    approveStatus: APPROVE_STATUS
    applicationTime: DT_RESPONSE
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[1-4]$")]
    grossAmount: str
    oriGrossAmount: str
    currency: CURRENCY
    taskId: CODE_18
    buyerTin: TIN
    buyerBusinessName: CODE_256
    buyerLegalName: CODE_256
    tin: TIN
    businessName: CODE_256
    legalName: CODE_256
    waitingDate: Annotated[int, Field(ge=0)]
    dataSource: DATA_SOURCE

class T111Response(BaseModel):
    page: T106Page
    records: List[T111Record]

# =========================================================
# T112: CREDIT NOTE APPLICATION DETAILS
# =========================================================
class T112Request(BaseModel):
    id: CODE_20

class T112GoodsItem(BaseModel):
    itemName: CODE_60
    itemCode: CODE_50
    qty: AMOUNT_20_8
    unit: CODE_20
    unitPrice: AMOUNT_20_8
    total: AMOUNT_SIGNED_16_2
    taxRate: RATE_12_8
    tax: AMOUNT_SIGNED_16_2
    discountTotal: Optional[AMOUNT_SIGNED_16_2] = None
    discountTaxRate: Optional[RATE_12_8] = None
    orderNumber: int
    discountFlag: DISCOUNT_FLAG
    deemedFlag: DEEMED_FLAG
    exciseFlag: EXCISE_FLAG
    categoryId: Optional[CODE_18] = None
    categoryName: Optional[CODE_1024] = None
    goodsCategoryId: CODE_18
    goodsCategoryName: CODE_200
    exciseRate: Optional[CODE_21] = None
    exciseRule: Optional[EXCISE_RULE] = None
    exciseTax: Optional[AMOUNT_SIGNED_16_2] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    exciseUnit: Optional[CODE_3] = None
    exciseCurrency: Optional[CURRENCY] = None
    exciseRateName: Optional[CODE_100] = None
    vatApplicableFlag: Optional[VAT_APPLICABLE] = "1"

CODE_60 = Annotated[str, Field(min_length=1, max_length=60)]

class T112Summary(BaseModel):
    netAmount: AMOUNT_SIGNED_16_2
    taxAmount: AMOUNT_SIGNED_16_2
    grossAmount: AMOUNT_SIGNED_16_2
    previousNetAmount: AMOUNT_16_2
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
    reason: CODE_1024
    selectRefundReasonCode: REASON_CODE
    approveStatusCode: APPROVE_STATUS
    updateTime: DT_RESPONSE
    applicationTime: DT_RESPONSE
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[1-4]$")]
    contactName: Optional[CODE_200] = None
    contactMobileNum: Optional[CODE_30] = None
    contactEmail: Optional[CODE_50] = None
    source: DATA_SOURCE
    taskId: Optional[CODE_18] = None
    remarks: Optional[CODE_500] = None
    grossAmount: str
    totalAmount: str
    currency: CURRENCY
    refundIssuedDate: Optional[DT_RESPONSE] = None
    issuedDate: DT_RESPONSE
    tin: TIN
    sellersReferenceNo: Optional[CODE_50] = None
    nin: NIN_BRN
    legalName: CODE_256
    businessName: CODE_256
    mobilePhone: Optional[CODE_30] = None
    address: Optional[CODE_500] = None
    emailAddress: Optional[CODE_50] = None
    buyerTin: Optional[TIN] = None
    buyerNin: Optional[NIN_BRN] = None
    buyerLegalName: Optional[CODE_256] = None
    buyerBusinessName: Optional[CODE_256] = None
    buyerAddress: Optional[CODE_500] = None
    buyerEmailAddress: Optional[CODE_50] = None
    buyerMobilePhone: Optional[CODE_30] = None
    buyerLinePhone: Optional[CODE_30] = None
    buyerCitizenship: Optional[CODE_128] = None
    buyerPassportNum: Optional[CODE_20] = None
    buyerPlaceOfBusi: Optional[CODE_500] = None
    goodsDetails: Optional[List[T112GoodsItem]] = None
    taxDetails: Optional[List[T108TaxDetail]] = None
    summary: Optional[T112Summary] = None
    payWay: Optional[List[T108PayWay]] = None
    basicInformation: Optional[T112BasicInformation] = None
    importServicesSeller: Optional[T108ImportServicesSeller] = None
    attachmentList: Optional[List[T110Attachment]] = None

# =========================================================
# T113: CREDIT NOTE APPROVAL
# =========================================================
class T113Request(BaseModel):
    referenceNo: CODE_20
    approveStatus: APPROVE_STATUS
    taskId: CODE_20
    remark: CODE_1024

# =========================================================
# T114: CANCEL CREDIT/DEBIT NOTE APPLICATION
# =========================================================
class T114Request(BaseModel):
    oriInvoiceId: CODE_20
    invoiceNo: CODE_20
    reason: Optional[CODE_1024] = None
    reasonCode: REASON_CODE
    invoiceApplyCategoryCode: Annotated[str, Field(pattern=r"^10[3-5]$")]
    attachmentList: Optional[List[T110Attachment]] = None

# =========================================================
# T115: SYSTEM DICTIONARY UPDATE
# =========================================================
class T115DictionaryValue(BaseModel):
    value: CODE_50
    name: CODE_200

class T115CustomsUnit(BaseModel):
    value: CODE_3
    name: CODE_200
    validPeriodFrom: DATE_RESPONSE
    periodTo: DATE_RESPONSE

class T115Format(BaseModel):
    dateFormat: str
    timeFormat: str

class T115Response(BaseModel):
    creditNoteMaximumInvoicingDays: Optional[T115DictionaryValue] = None
    currencyType: Optional[List[T115DictionaryValue]] = None
    creditNoteValuePercentLimit: Optional[T115DictionaryValue] = None
    rateUnit: Optional[List[T115DictionaryValue]] = None
    format: Optional[T115Format] = None
    sector: Optional[List[Dict[str, str]]] = None
    payWay: Optional[List[T115DictionaryValue]] = None
    countryCode: Optional[List[T115DictionaryValue]] = None
    customsPackUnitList: Optional[List[T115CustomsUnit]] = None  # V23.7
    customsPieceUnitList: Optional[List[T115CustomsUnit]] = None  # V23.7
    deliveryTerms: Optional[List[T115DictionaryValue]] = None

# =========================================================
# T116: Z-REPORT DAILY UPLOAD
# =========================================================
class T116Request(BaseModel):
    deviceNo: DEVICE_NO
    reportDate: DATE_REQUEST
    # Other fields TBD per spec

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
# T118: QUERY CREDIT NOTE APPLICATION DETAILS
# =========================================================
class T118Request(BaseModel):
    id: CODE_20

class T118Summary(BaseModel):
    netAmount: str
    taxAmount: str
    grossAmount: str
    previousNetAmount: str
    previousTaxAmount: str
    previousGrossAmount: str

class T118BasicInformation(BaseModel):
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    invoiceIndustryCode: Optional[INDUSTRY_CODE] = None

class T118Response(BaseModel):
    goodsDetails: List[T112GoodsItem]
    taxDetails: List[T108TaxDetail]
    summary: T118Summary
    payWay: Optional[List[T108PayWay]] = None
    basicInformation: Optional[T118BasicInformation] = None

# =========================================================
# T119: QUERY TAXPAYER INFORMATION BY TIN
# =========================================================
class T119Request(BaseModel):
    tin: Optional[TIN] = None
    ninBrn: Optional[NIN_BRN] = None

class T119Taxpayer(BaseModel):
    address: CODE_500
    businessName: CODE_256
    contactEmail: CODE_50
    contactNumber: CODE_50
    governmentTIN: Annotated[str, Field(pattern=r"^[01]$")]
    legalName: CODE_256
    taxpayerStatus: CODE_3
    taxpayerType: CODE_3
    tin: TIN

class T119Response(BaseModel):
    taxpayer: T119Taxpayer

# =========================================================
# T120: VOID CREDIT DEBIT/NOTE APPLICATION
# =========================================================
class T120Request(BaseModel):
    businessKey: CODE_20
    referenceNo: CODE_20

# =========================================================
# T121: ACQUIRING EXCHANGE RATE
# =========================================================
class T121Request(BaseModel):
    currency: CURRENCY
    issueDate: Optional[DATE_REQUEST] = None

class T121Response(BaseModel):
    currency: CURRENCY
    rate: str
    importDutyLevy: str
    inComeTax: str
    exportLevy: str

# =========================================================
# T122: QUERY CANCEL CREDIT NOTE DETAILS
# =========================================================
class T122Request(BaseModel):
    invoiceNo: CODE_20

class T122Response(BaseModel):
    invoiceNo: CODE_20
    currency: CURRENCY
    issueDate: DT_RESPONSE
    grossAmount: str
    reason: CODE_1024
    reasonCode: REASON_CODE

# =========================================================
# T123/T124/T134: COMMODITY CATEGORY
# =========================================================
class T123CommodityCategory(BaseModel):
    commodityCategoryCode: CODE_18
    parentCode: CODE_18
    commodityCategoryName: CODE_200
    commodityCategoryLevel: Annotated[int, Field(ge=1)]
    rate: RATE_12_8
    isLeafNode: IS_LEAF_NODE
    serviceMark: SERVICE_MARK
    isZeroRate: IS_LEAF_NODE
    zeroRateStartDate: Optional[DATE_RESPONSE] = None
    zeroRateEndDate: Optional[DATE_RESPONSE] = None
    isExempt: IS_LEAF_NODE
    exemptRateStartDate: Optional[DATE_RESPONSE] = None
    exemptRateEndDate: Optional[DATE_RESPONSE] = None
    enableStatusCode: ENABLE_STATUS
    exclusion: EXCLUSION_TYPE
    excisable: Optional[IS_LEAF_NODE] = None
    vatOutScopeCode: Optional[CODE_3] = None

class T124Request(BaseModel):
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20

class T124Response(BaseModel):
    page: T106Page
    records: List[T123CommodityCategory]

class T134Request(BaseModel):
    commodityCategoryVersion: CODE_20

class T134Response(RootModel[List[T123CommodityCategory]]):
    pass

# =========================================================
# T125: QUERY EXCISE DUTY
# =========================================================
class T125ExciseDutyDetail(BaseModel):
    exciseDutyId: CODE_18
    type: Annotated[str, Field(pattern=r"^10[12]$")]
    rate: Optional[CODE_21] = None
    unit: Optional[CODE_3] = None
    currency: Optional[CURRENCY] = None

class T125ExciseDuty(BaseModel):
    id: CODE_20
    exciseDutyCode: CODE_20
    goodService: CODE_500
    parentCode: CODE_20
    rateText: CODE_50
    isLeafNode: IS_LEAF_NODE
    effectiveDate: DATE_RESPONSE
    exciseDutyDetailsList: List[T125ExciseDutyDetail]

class T125Response(BaseModel):
    exciseDutyList: List[T125ExciseDuty]

# =========================================================
# T126: GET ALL EXCHANGE RATES
# =========================================================
class T126ExchangeRate(BaseModel):
    currency: CURRENCY
    rate: str
    importDutyLevy: str
    inComeTax: str
    exportLevy: str

class T126Response(RootModel[List[T126ExchangeRate]]):
    pass

# =========================================================
# T127: GOODS/SERVICES INQUIRY
# =========================================================
class T127Request(BaseModel):
    goodsCode: Optional[CODE_50] = None
    goodsName: Optional[CODE_200] = None
    commodityCategoryName: Optional[CODE_200] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20
    branchId: Optional[CODE_18] = None
    serviceMark: Optional[SERVICE_MARK] = None
    haveExciseTax: Optional[HAVE_EXCISE] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    combineKeywords: Optional[CODE_50] = None
    goodsTypeCode: Optional[CODE_3] = "101"
    tin: Optional[TIN] = None
    queryType: Optional[QUERY_TYPE] = "1"

class T127CustomsUnit(BaseModel):
    id: Optional[CODE_18] = None
    commodityGoodsId: Optional[CODE_18] = None
    customsMeasureUnit: CODE_3
    customsUnitPrice: AMOUNT_20_8
    packageScaledValueCustoms: AMOUNT_20_8
    customsScaledValue: AMOUNT_20_8

class T127GoodsOtherUnit(BaseModel):
    id: Optional[CODE_18] = None
    commodityGoodsId: Optional[CODE_18] = None
    otherScaled: AMOUNT_20_8
    otherUnit: CODE_3
    otherPrice: AMOUNT_20_8
    packageScaled: AMOUNT_20_8

class T127CommodityGoodsExtendEntity(BaseModel):
    customsMeasureUnit: CODE_3
    customsUnitPrice: AMOUNT_20_8
    packageScaledValueCustoms: AMOUNT_20_8
    customsScaledValue: AMOUNT_20_8

class T127GoodsRecord(BaseModel):
    id: CODE_18
    goodsName: CODE_100
    goodsCode: CODE_50
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    currency: CURRENCY
    stock: Annotated[int, Field(ge=0)]
    stockPrewarning: Annotated[int, Field(ge=0)]
    source: Annotated[str, Field(pattern=r"^10[12]$")]
    statusCode: Annotated[str, Field(pattern=r"^10[12]$")]
    commodityCategoryCode: CODE_18
    commodityCategoryName: CODE_200
    taxRate: RATE_12_8
    isZeroRate: IS_LEAF_NODE
    isExempt: IS_LEAF_NODE
    haveExciseTax: HAVE_EXCISE
    exciseDutyCode: Optional[CODE_20] = None
    exciseDutyName: Optional[CODE_100] = None
    exciseRate: Optional[CODE_21] = None
    pack: Optional[AMOUNT_20_8] = None
    stick: Optional[AMOUNT_20_8] = None
    remarks: Optional[CODE_1024] = None
    packageScaledValue: Optional[AMOUNT_20_8] = None
    pieceScaledValue: Optional[AMOUNT_20_8] = None
    pieceMeasureUnit: Optional[CODE_3] = None
    havePieceUnit: HAVE_PIECE
    pieceUnitPrice: Optional[AMOUNT_20_8] = None
    exclusion: EXCLUSION_TYPE
    haveOtherUnit: HAVE_OTHER
    serviceMark: SERVICE_MARK
    goodsTypeCode: CODE_3
    updateDateStr: Optional[DT_REQUEST] = None
    tankNo: Optional[CODE_50] = None
    haveCustomsUnit: HAVE_CUSTOMS
    commodityGoodsExtendEntity: Optional[T127CommodityGoodsExtendEntity] = None  # V23.4+
    customsUnitList: Optional[List[T127CustomsUnit]] = None  # V23.7
    goodsOtherUnits: Optional[List[T127GoodsOtherUnit]] = None

class T127Response(BaseModel):
    page: T106Page
    records: List[T127GoodsRecord]

# =========================================================
# T128: QUERY STOCK BY GOODS ID
# =========================================================
class T128Request(BaseModel):
    id: CODE_18
    branchId: Optional[CODE_18] = None

class T128Response(BaseModel):
    stock: Annotated[int, Field(ge=0)]
    stockPrewarning: Annotated[int, Field(ge=0)]

# =========================================================
# T129: BATCH INVOICE UPLOAD
# =========================================================
class T129InvoiceItem(BaseModel):
    invoiceContent: str  # T109 Request JSON string
    invoiceSignature: str

class T129Request(RootModel[List[T129InvoiceItem]]):
    pass

class T129ResultItem(BaseModel):
    invoiceContent: str  # T109 Response JSON string
    invoiceReturnCode: CODE_2
    invoiceReturnMessage: Optional[CODE_500] = None

class T129Response(RootModel[List[T129ResultItem]]):
    pass

# =========================================================
# T130: GOODS UPLOAD
# =========================================================
class T130CustomsUnit(BaseModel):
    customsMeasureUnit: CODE_3
    customsUnitPrice: AMOUNT_20_8
    packageScaledValueCustoms: AMOUNT_20_8
    customsScaledValue: AMOUNT_20_8

class T130GoodsItem(BaseModel):
    operationType: Optional[OPERATION_TYPE] = "101"
    goodsName: CODE_100
    goodsCode: CODE_50
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    currency: CURRENCY
    commodityCategoryId: CODE_18
    haveExciseTax: HAVE_EXCISE
    description: Optional[CODE_1024] = None
    stockPrewarning: Annotated[int, Field(ge=0)]
    pieceMeasureUnit: Optional[CODE_3] = None
    havePieceUnit: Optional[HAVE_PIECE] = None
    pieceUnitPrice: Optional[AMOUNT_20_8] = None
    packageScaledValue: Optional[AMOUNT_20_8] = None
    pieceScaledValue: Optional[AMOUNT_20_8] = None
    exciseDutyCode: Optional[CODE_20] = None
    haveOtherUnit: Optional[HAVE_OTHER] = None
    goodsTypeCode: Optional[CODE_3] = "101"
    haveCustomsUnit: HAVE_CUSTOMS
    commodityGoodsExtendEntity: Optional[T127CommodityGoodsExtendEntity] = None  # V23.4+
    customsUnitList: Optional[List[T130CustomsUnit]] = None  # V23.7
    goodsOtherUnits: Optional[List[T127GoodsOtherUnit]] = None

class T130GoodsResult(BaseModel):
    operationType: Optional[OPERATION_TYPE] = None
    goodsName: CODE_100
    goodsCode: CODE_50
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    currency: CURRENCY
    commodityCategoryId: CODE_18
    haveExciseTax: HAVE_EXCISE
    description: Optional[CODE_1024] = None
    stockPrewarning: Annotated[int, Field(ge=0)]
    pieceMeasureUnit: Optional[CODE_3] = None
    havePieceUnit: Optional[HAVE_PIECE] = None
    pieceUnitPrice: Optional[AMOUNT_20_8] = None
    packageScaledValue: Optional[AMOUNT_20_8] = None
    pieceScaledValue: Optional[AMOUNT_20_8] = None
    exciseDutyCode: Optional[CODE_20] = None
    haveOtherUnit: Optional[HAVE_OTHER] = None
    goodsTypeCode: Optional[CODE_3] = None
    haveCustomsUnit: Optional[HAVE_CUSTOMS] = None
    commodityGoodsExtendEntity: Optional[T127CommodityGoodsExtendEntity] = None
    goodsOtherUnits: Optional[List[T127GoodsOtherUnit]] = None
    returnCode: Optional[CODE_4] = None
    returnMessage: Optional[CODE_500] = None

CODE_4 = Annotated[str, Field(min_length=1, max_length=4)]

class T130Request(RootModel[List[T130GoodsItem]]):
    pass

class T130Response(RootModel[List[T130GoodsResult]]):
    pass

# =========================================================
# T131: GOODS STOCK MAINTAIN
# =========================================================
class T131StockItem(BaseModel):
    commodityGoodsId: CODE_18
    goodsCode: Optional[CODE_50] = None
    measureUnit: CODE_3
    quantity: AMOUNT_20_8
    unitPrice: AMOUNT_20_8
    remarks: Optional[CODE_1024] = None
    fuelTankId: Optional[CODE_18] = None
    lossQuantity: Optional[AMOUNT_20_8] = None
    originalQuantity: Optional[AMOUNT_20_8] = None

class T131StockResult(BaseModel):
    commodityGoodsId: CODE_18
    goodsCode: CODE_50
    measureUnit: CODE_3
    quantity: AMOUNT_20_8
    unitPrice: AMOUNT_20_8
    remarks: Optional[CODE_1024] = None
    fuelTankId: Optional[CODE_18] = None
    lossQuantity: Optional[AMOUNT_20_8] = None
    originalQuantity: Optional[AMOUNT_20_8] = None
    returnCode: Optional[CODE_4] = None
    returnMessage: Optional[CODE_500] = None

class T131GoodsStockIn(BaseModel):
    operationType: OPERATION_TYPE
    supplierTin: Optional[TIN] = None
    supplierName: Optional[CODE_100] = None
    adjustType: Optional[CODE_20] = None
    remarks: Optional[CODE_1024] = None
    stockInDate: DATE_REQUEST
    stockInType: STOCK_IN_TYPE
    productionBatchNo: Optional[CODE_50] = None
    productionDate: Optional[DATE_REQUEST] = None
    branchId: CODE_18
    invoiceNo: Optional[CODE_20] = None
    isCheckBatchNo: Optional[Annotated[str, Field(pattern=r"^[01]$")]] = "0"
    rollBackIfError: Optional[Annotated[str, Field(pattern=r"^[01]$")]] = "0"
    goodsTypeCode: Optional[CODE_3] = "101"

class T131Request(BaseModel):
    goodsStockIn: T131GoodsStockIn
    goodsStockInItem: List[T131StockItem]

class T131Response(RootModel[List[T131StockResult]]):
    pass

# =========================================================
# T132: UPLOAD EXCEPTION LOG
# =========================================================
class T132ExceptionLog(BaseModel):
    interruptionTypeCode: Annotated[str, Field(pattern=r"^10[1-5]$")]
    description: CODE_1024
    errorDetail: Optional[CODE_4000] = None
    interruptionTime: DT_REQUEST

class T132Request(RootModel[List[T132ExceptionLog]]):
    pass

# =========================================================
# T133: TCS UPGRADE SYSTEM FILE DOWNLOAD
# =========================================================
class T133Request(BaseModel):
    tcsVersion: str
    osType: Annotated[str, Field(pattern=r"^[01]$")]

class T133File(BaseModel):
    updatefile: str
    iszip: Optional[str] = None
    updateurl: str
    deleteurl: str
    ordernumber: str

class T133Sql(BaseModel):
    updatesql: str
    ordernumer: int

class T133Response(BaseModel):
    precommand: str
    precommandurl: str
    precommandfilename: Optional[CODE_500] = None
    command: str
    commandurl: str
    commandfilename: Optional[CODE_500] = None
    tcsversion: str
    fileList: List[T133File]
    sqlList: List[T133Sql]

# =========================================================
# T135: GET TCS LATEST VERSION
# =========================================================
class T135Response(BaseModel):
    latesttcsversion: str

# =========================================================
# T136: CERTIFICATE PUBLIC KEY UPLOAD
# =========================================================
class T136Request(BaseModel):
    fileName: CODE_256
    verifyString: str
    fileContent: str  # Base64

# =========================================================
# T137: CHECK EXEMPT/DEEMED TAXPAYER
# =========================================================
class T137Request(BaseModel):
    tin: TIN
    commodityCategoryCode: Optional[CODE_100] = None  # Comma separated

class T137Project(BaseModel):
    projectId: CODE_18
    projectName: CODE_100
    deemedExemptCode: CODE_3
    commodityCategoryCode: CODE_18
    serviceMark: SERVICE_MARK
    unit: CODE_3
    currentQty: Optional[str] = None
    currentAmount: Optional[str] = None
    currency: Optional[CURRENCY] = None  # V23.5
    exchangeRateDate: Optional[DATE_REQUEST] = None  # V23.5
    currentAmountCurrency: Optional[str] = None  # V23.5

class T137Category(BaseModel):
    commodityCategoryCode: CODE_18
    commodityCategoryTaxpayerType: CODE_3

class T137Response(BaseModel):
    taxpayerType: CODE_3
    exemptType: Optional[CODE_3] = None
    commodityCategory: Optional[List[T137Category]] = None
    deemedAndExemptProjectList: Optional[List[T137Project]] = None

# =========================================================
# T138: GET ALL BRANCHES
# =========================================================
class T138Branch(BaseModel):
    branchId: CODE_18
    branchName: CODE_500

class T138Request(BaseModel):
    tin: Optional[TIN] = None

class T138Response(RootModel[List[T138Branch]]):
    pass

# =========================================================
# T139: GOODS STOCK TRANSFER
# =========================================================
class T139TransferItem(BaseModel):
    commodityGoodsId: CODE_18
    goodsCode: Optional[CODE_50] = None
    measureUnit: CODE_3
    quantity: AMOUNT_20_8
    remarks: Optional[CODE_1024] = None
    sourceFuelTankId: Optional[CODE_18] = None
    destinationFuelTankId: Optional[CODE_18] = None

class T139TransferResult(BaseModel):
    commodityGoodsId: CODE_18
    measureUnit: CODE_3
    quantity: AMOUNT_20_8
    remarks: Optional[CODE_1024] = None
    sourceFuelTankId: Optional[CODE_18] = None
    destinationFuelTankId: Optional[CODE_18] = None
    returnCode: Optional[CODE_4] = None
    returnMessage: Optional[CODE_500] = None

class T139GoodsStockTransfer(BaseModel):
    sourceBranchId: CODE_18
    destinationBranchId: CODE_18
    transferTypeCode: TRANSFER_TYPE
    remarks: Optional[CODE_1024] = None
    rollBackIfError: Optional[Annotated[str, Field(pattern=r"^[01]$")]] = "0"
    goodsTypeCode: Optional[CODE_3] = "101"

class T139Request(BaseModel):
    goodsStockTransfer: T139GoodsStockTransfer
    goodsStockTransferItem: List[T139TransferItem]

class T139Response(RootModel[List[T139TransferResult]]):
    pass

# =========================================================
# T144: QUERY GOODS BY CODE
# =========================================================
class T144Request(BaseModel):
    goodsCode: CODE_50  # Comma separated
    tin: Optional[TIN] = None

class T144Response(BaseModel):
    goodsCode: CODE_50
    measureUnit: CODE_3
    havePieceUnit: HAVE_PIECE
    pieceMeasureUnit: Optional[CODE_3] = None
    haveOtherUnit: HAVE_OTHER
    packageScaledValue: AMOUNT_20_8
    pieceScaledValue: AMOUNT_20_8
    goodsOtherUnits: Optional[List[T127GoodsOtherUnit]] = None

# =========================================================
# T145-T149: STOCK RECORDS QUERIES (Simplified Structures)
# =========================================================
class T145Request(BaseModel):
    productionBatchNo: Optional[CODE_50] = None
    invoiceNo: Optional[CODE_20] = None
    referenceNo: Optional[CODE_50] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20

class T145Record(BaseModel):
    supplierTin: Optional[TIN] = None
    supplierName: Optional[CODE_100] = None
    adjustType: Optional[CODE_3] = None
    remarks: Optional[CODE_1024] = None
    stockInDate: Optional[DATE_REQUEST] = None
    stockInType: Optional[STOCK_IN_TYPE] = None
    productionBatchNo: Optional[CODE_50] = None
    productionDate: Optional[DATE_REQUEST] = None
    branchId: Optional[CODE_18] = None
    invoiceNo: Optional[CODE_20] = None
    referenceNo: Optional[CODE_50] = None
    branchName: Optional[CODE_500] = None
    totalAmount: Optional[str] = None

class T145Response(BaseModel):
    page: T106Page
    records: List[T145Record]

class T147Request(BaseModel):
    combineKeywords: Optional[CODE_50] = None
    stockInType: Optional[STOCK_IN_TYPE] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20
    supplierTin: Optional[TIN] = None
    supplierName: Optional[CODE_100] = None

class T147Response(BaseModel):
    page: T106Page
    records: List[T145Record]  # Reuses structure

class T148Request(BaseModel):
    id: CODE_18

class T148GoodsStockIn(BaseModel):
    stockInType: STOCK_IN_TYPE
    remarks: Optional[CODE_1024] = None
    invoiceNo: Optional[CODE_20] = None
    branchId: CODE_18
    branchName: CODE_500
    stockInDate: DATE_REQUEST
    supplierTin: TIN
    supplierName: CODE_100
    productionBatchNo: Optional[CODE_50] = None
    productionDate: Optional[DATE_REQUEST] = None

class T148GoodsItem(BaseModel):
    commodityGoodsId: CODE_18
    goodsCode: CODE_50
    goodsName: CODE_600
    measureUnit: CODE_3
    currency: CURRENCY
    quantity: AMOUNT_20_8
    unitPrice: AMOUNT_20_8
    amount: str

CODE_600 = Annotated[str, Field(min_length=1, max_length=600)]

class T148Response(BaseModel):
    goodsStockIn: T148GoodsStockIn
    goodsStockInGoods: List[T148GoodsItem]

class T149Request(BaseModel):
    referenceNo: Optional[CODE_50] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20

class T149Record(BaseModel):
    id: CODE_18
    referenceNo: CODE_50
    branchName: CODE_500
    adjustDate: DATE_REQUEST
    adjustType: CODE_3
    remarks: Optional[CODE_1024] = None
    adjustAmount: str

class T149Response(BaseModel):
    page: T106Page
    records: List[T149Record]

class T160Request(BaseModel):
    id: CODE_18

class T160GoodsAdjust(BaseModel):
    branchId: CODE_18
    branchName: CODE_500
    adjustDate: DATE_REQUEST
    adjustType: CODE_3
    remarks: Optional[CODE_1024] = None
    adjustAmount: str

class T160GoodsItem(BaseModel):
    commodityGoodsId: CODE_18
    goodsCode: CODE_50
    goodsName: CODE_600
    measureUnit: CODE_3
    unitPrice: AMOUNT_20_8
    stock: AMOUNT_20_8
    adjustQuantity: AMOUNT_20_8
    currentQuantity: AMOUNT_20_8
    adjustAmount: str
    remarks: Optional[CODE_1024] = None

class T160Response(BaseModel):
    goodsStockAdjust: T160GoodsAdjust
    goodsStocAdjustGoods: List[T160GoodsItem]

# =========================================================
# T162-T177: EDC / FUEL SPECIFIC (Selected Key Models)
# =========================================================
class T162Response(BaseModel):
    fuelTypeCode: CODE_18
    parentCode: CODE_18
    fuelTypeName: CODE_200
    fuelTypeLevel: CODE_1
    isLeafNode: IS_LEAF_NODE

class T163Request(BaseModel):
    shiftNo: CODE_20
    startVolume: str
    endVolume: str
    fuelType: CODE_200
    goodsId: CODE_18
    goodsCode: CODE_50
    invoiceAmount: str
    invoiceNumber: CODE_50
    nozzleNo: CODE_50
    pumpNo: CODE_50
    tankNo: CODE_50
    userName: CODE_500
    userCode: CODE_100
    startTime: DT_REQUEST
    endTime: DT_REQUEST

class T164Request(BaseModel):
    deviceNumber: CODE_50
    disconnectedType: CODE_3
    disconnectedTime: DT_REQUEST
    remarks: Optional[str] = None

class T166Request(BaseModel):
    invoiceNo: CODE_20
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerPassportNum: Optional[CODE_20] = None
    buyerLegalName: Optional[CODE_256] = None
    buyerBusinessName: Optional[CODE_256] = None
    buyerAddress: Optional[CODE_500] = None
    buyerEmailAddress: Optional[CODE_50] = None
    buyerMobilePhone: Optional[CODE_30] = None
    buyerLinePhone: Optional[CODE_30] = None
    buyerPlaceOfBusi: Optional[CODE_500] = None
    buyerType: BUYER_TYPE
    buyerCitizenship: Optional[CODE_128] = None
    buyerSector: Optional[CODE_200] = None
    mvrn: Optional[CODE_32] = None
    createDateStr: Optional[DT_REQUEST] = None

class T167Request(BaseModel):
    fuelType: Optional[CODE_200] = None
    invoiceNo: Optional[CODE_20] = None
    buyerLegalName: Optional[CODE_256] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20
    queryType: Annotated[str, Field(pattern=r"^[1-3]$")] = "1"
    branchId: Optional[CODE_18] = None

class T167Record(BaseModel):
    id: CODE_32
    invoiceNo: CODE_30
    oriInvoiceId: Optional[CODE_32] = None
    oriInvoiceNo: Optional[CODE_30] = None
    issuedDate: DT_RESPONSE
    buyerTin: TIN
    buyerLegalName: CODE_256
    buyerNinBrn: NIN_BRN
    currency: CURRENCY
    grossAmount: str
    taxAmount: str
    dataSource: DATA_SOURCE
    isInvalid: YN
    isRefund: Annotated[str, Field(pattern=r"^[012]$")]
    invoiceType: INVOICE_TYPE
    invoiceKind: INVOICE_KIND
    invoiceIndustryCode: INDUSTRY_CODE
    branchName: CODE_500
    deviceNo: DEVICE_NO
    uploadingTime: DT_RESPONSE
    referenceNo: Optional[CODE_50] = None
    operator: CODE_100
    userName: CODE_500
    pumpNo: CODE_50
    nozzleNo: CODE_50
    fuelType: CODE_200
    updateTimes: str

class T167Response(BaseModel):
    page: T106Page
    records: List[T167Record]

class T170Request(BaseModel):
    deviceNumber: DEVICE_NO
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None

class T170Record(BaseModel):
    deviceNumber: DEVICE_NO
    longitude: CODE_60
    latitude: CODE_60
    recordDate: DATE_RESPONSE

class T170Response(RootModel[List[T170Record]]):
    pass

class T172Request(BaseModel):
    nozzleId: CODE_18
    nozzleNo: CODE_50
    status: CODE_1

class T175Request(BaseModel):
    tin: TIN
    mobileNumber: CODE_30

class T176Request(BaseModel):
    deviceNo: DEVICE_NO
    deviceIssuingStatus: CODE_3

class T177Response(BaseModel):
    goodsStockLimit: Dict[str, Any]
    goodsStockLimitCategoryList: List[Dict[str, Any]]

# =========================================================
# T178-T187: AGENT / TRANSFER / HS / STATUS
# =========================================================
class T178Request(BaseModel):
    destinationBranchId: CODE_18
    remarks: Optional[CODE_1024] = None

class T179Request(BaseModel):
    tin: TIN

class T179AgentTaxpayer(BaseModel):
    taxpayerId: CODE_18
    tin: TIN
    ninBrn: NIN_BRN
    legalName: CODE_256
    businessName: CODE_256
    contactNumber: CODE_50
    contactEmail: CODE_50
    address: CODE_500
    taxpayerType: CODE_3
    taxpayerStatus: CODE_3
    branchId: CODE_18
    branchCode: CODE_50
    branchName: CODE_500
    branchStatus: CODE_3

class T179Response(BaseModel):
    agentTaxpayerList: List[T179AgentTaxpayer]

class T180Request(BaseModel):
    tin: TIN
    branchId: CODE_18

class T180Response(BaseModel):
    taxType: List[T103TaxType]
    issueTaxTypeRestrictions: Annotated[str, Field(pattern=r"^[01]$")]
    sellersLogo: Optional[str] = None
    isAllowBackDate: Annotated[str, Field(pattern=r"^[01]$")]
    isDutyFreeTaxpayer: Annotated[str, Field(pattern=r"^[01]$")]
    periodDate: str
    isAllowIssueInvoice: Annotated[str, Field(pattern=r"^[01]$")]
    isAllowOutOfScopeVAT: Annotated[str, Field(pattern=r"^[01]$")]

class T181Request(BaseModel):
    operationType: Annotated[str, Field(pattern=r"^10[1-3]$")]
    id: Optional[CODE_18] = None
    buyerType: BUYER_TYPE
    buyerTin: Optional[TIN] = None
    buyerNinBrn: Optional[NIN_BRN] = None
    buyerLegalName: CODE_256
    buyerBusinessName: Optional[CODE_256] = None
    buyerEmail: Optional[CODE_50] = None
    buyerLinePhone: Optional[CODE_30] = None
    buyerAddress: Optional[CODE_500] = None
    buyerCitizenship: Optional[CODE_128] = None
    buyerPassportNum: Optional[CODE_30] = None

class T182Request(BaseModel):
    buyerTin: Optional[TIN] = None
    buyerLegalName: Optional[CODE_256] = None

class T182Record(BaseModel):
    id: CODE_18
    buyerType: BUYER_TYPE
    buyerTin: TIN
    buyerNinBrn: NIN_BRN
    buyerLegalName: CODE_256
    buyerBusinessName: CODE_256
    buyerEmail: CODE_50
    buyerLinePhone: CODE_30
    buyerAddress: CODE_500
    buyerCitizenship: CODE_128
    buyerPassportNum: CODE_30

class T182Response(RootModel[List[T182Record]]):
    pass

class T183Request(BaseModel):
    referenceNo: Optional[CODE_50] = None
    sourceBranchId: Optional[CODE_18] = None
    destinationBranchId: Optional[CODE_18] = None
    startDate: Optional[DATE_REQUEST] = None
    endDate: Optional[DATE_REQUEST] = None
    pageNo: Annotated[int, Field(ge=1)] = 1
    pageSize: Annotated[int, Field(ge=1, le=100)] = 20

class T183Record(BaseModel):
    id: CODE_18
    referenceNo: CODE_50
    sourceBranchName: CODE_500
    destinationBranchName: CODE_500
    transferAmount: str
    transferDate: DATE_RESPONSE

class T183Response(BaseModel):
    page: T106Page
    records: List[T183Record]

class T184Request(BaseModel):
    id: CODE_18

class T184Transfer(BaseModel):
    sourceBranchId: CODE_18
    destinationBranchId: CODE_18
    transferDate: DATE_RESPONSE
    transferTypeCode: TRANSFER_TYPE
    remarks: Optional[CODE_1024] = None

class T184Item(BaseModel):
    commodityGoodsId: CODE_18
    goodsCode: CODE_50
    goodsName: CODE_600
    measureUnit: CODE_3
    currency: CURRENCY
    unitPrice: AMOUNT_20_8
    bookQuantity: AMOUNT_20_8
    transferQuantity: AMOUNT_20_8
    transferAmount: str
    currentQuantity: AMOUNT_20_8
    remarks: Optional[CODE_1024] = None

class T184Response(BaseModel):
    goodsStockTransfer: T184Transfer
    goodsStockTransferItem: List[T184Item]

class T185Response(BaseModel):
    hsCode: CODE_20
    description: CODE_20
    isLeaf: CODE_1
    parentClass: CODE_20

class T186Request(BaseModel):
    invoiceNo: CODE_20

class T186Response(BaseModel):
    # Similar to T108Response but includes remainQty/remainAmount in goodsDetails
    sellerDetails: T108SellerDetails
    basicInformation: T108BasicInformation
    buyerDetails: T108BuyerDetails
    buyerExtend: Optional[T108BuyerExtend] = None
    goodsDetails: List[T108GoodsItem]  # Doc says remainQty/Amount added here
    taxDetails: List[T108TaxDetail]
    summary: T108Summary
    payWay: Optional[List[T108PayWay]] = None
    extend: Optional[T108Extend] = None
    custom: Optional[T108Custom] = None
    importServicesSeller: Optional[T108ImportServicesSeller] = None
    airlineGoodsDetails: Optional[List[T108AirlineGoodsDetails]] = None
    edcDetails: Optional[T108EdcDetails] = None
    agentEntity: Optional[T108AgentEntity] = None

class T187Request(BaseModel):
    invoiceNo: CODE_50

class T187Response(BaseModel):
    invoiceNo: CODE_20
    documentStatusCode: CODE_3

# =========================================================
# SCHEMA REGISTRY
# =========================================================
SCHEMAS: Dict[str, Any] = {
    # System
    "T101": {"response": T101Response},
    "T102": {"request": T102Request, "response": T102Response},
    "T103": {"response": T103Response},
    "T104": {"response": T104Response},
    "T105": {"request": T105Request},
    # Invoice
    "T106": {"request": T106Request, "response": T106Response},
    "T107": {"request": T107Request, "response": T107Response},
    "T108": {"request": T108Request, "response": T108Response},
    "T109": {"request": T109BillingUpload, "response": T109Response},
    "T129": {"request": T129Request, "response": T129Response},
    # Credit/Debit
    "T110": {"request": T110CreditApplication, "response": T110Response},
    "T111": {"request": T111Request, "response": T111Response},
    "T112": {"request": T112Request, "response": T112Response},
    "T113": {"request": T113Request},
    "T114": {"request": T114Request},
    "T118": {"request": T118Request, "response": T118Response},
    "T120": {"request": T120Request},
    "T122": {"request": T122Request, "response": T122Response},
    # Taxpayer/Branch
    "T119": {"request": T119Request, "response": T119Response},
    "T137": {"request": T137Request, "response": T137Response},
    "T138": {"request": T138Request, "response": T138Response},
    "T180": {"request": T180Request, "response": T180Response},
    # Goods/Stock
    "T123": {"response": List[T123CommodityCategory]},
    "T124": {"request": T124Request, "response": T124Response},
    "T125": {"response": T125Response},
    "T126": {"request": T121Request, "response": T126Response}, # T121/T126 similar
    "T121": {"request": T121Request, "response": T121Response},
    "T127": {"request": T127Request, "response": T127Response},
    "T128": {"request": T128Request, "response": T128Response},
    "T130": {"request": T130Request, "response": T130Response},
    "T131": {"request": T131Request, "response": T131Response},
    "T134": {"request": T134Request, "response": T134Response},
    "T139": {"request": T139Request, "response": T139Response},
    "T144": {"request": T144Request, "response": T144Response},
    "T145": {"request": T145Request, "response": T145Response},
    "T147": {"request": T147Request, "response": T147Response},
    "T148": {"request": T148Request, "response": T148Response},
    "T149": {"request": T149Request, "response": T149Response},
    "T160": {"request": T160Request, "response": T160Response},
    "T183": {"request": T183Request, "response": T183Response},
    "T184": {"request": T184Request, "response": T184Response},
    # System/Utility
    "T115": {"response": T115Response},
    "T116": {"request": T116Request},
    "T117": {"request": T117Request, "response": T117Response},
    "T132": {"request": T132Request},
    "T133": {"request": T133Request, "response": T133Response},
    "T135": {"response": T135Response},
    "T136": {"request": T136Request},
    # EDC/Fuel
    "T162": {"response": List[T162Response]},
    "T163": {"request": T163Request},
    "T164": {"request": T164Request},
    "T166": {"request": T166Request},
    "T167": {"request": T167Request, "response": T167Response},
    "T170": {"request": T170Request, "response": T170Response},
    "T172": {"request": T172Request},
    "T175": {"request": T175Request},
    "T176": {"request": T176Request},
    "T177": {"response": T177Response},
    # Agent/Other
    "T178": {"request": T178Request},
    "T179": {"request": T179Request, "response": T179Response},
    "T181": {"request": T181Request},
    "T182": {"request": T182Request, "response": T182Response},
    "T185": {"response": List[T185Response]},
    "T186": {"request": T186Request, "response": T186Response},
    "T187": {"request": T187Request, "response": T187Response},
}