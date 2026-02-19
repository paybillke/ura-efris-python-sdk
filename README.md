<p align="center">
  <a href="https://paybill.ke" target="_blank">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://paybill.ke/logo-wordmark--dark.png">
      <img src="https://paybill.ke/logo-wordmark--light.png" width="180" alt="Paybill Kenya Logo">
    </picture>
  </a>
</p>

# URA EFRIS System-to-System Integration SDK (Python)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-3a56c5?logo=pydantic)
![License](https://img.shields.io/badge/License-MIT-green)
![URA EFRIS](https://img.shields.io/badge/URA-EFRIS-2E8B57)
![Postman Compliant](https://img.shields.io/badge/Postman-Compliant-FF6C37?logo=postman)
![Pytest Tested](https://img.shields.io/badge/Tests-Pytest-3776AB?logo=pytest)

A production-ready **Python SDK** for integrating with the Uganda Revenue Authority (URA) **EFRIS** (Electronic Fiscal Receipting and Invoicing System) via the **System-to-System (S2S)** interface.  
Built in accordance with official URA EFRIS technical specifications, encryption standards, device registration requirements, and offline mode enablement guidelines.

---

## Official URA EFRIS Documentation

📄 **Step-by-Step Guide – System-to-System Integration (v1.1)**  
Issue Date: 19/07/2022  
https://efris.ura.go.ug/site/manualDownload/downloadManualById?id=569326253531712032&language=

📄 **Offline-Mode Enabler – Hardware & Software Requirements**  
https://efris.ura.go.ug/site/manualDownload/downloadManualById?id=779571457750410225&language=

📄 **Offline-Mode Enabler – Installation Guide**  
https://efris.ura.go.ug/site/manualDownload/downloadManualById?id=537308370255165978&language=

📄 **Interface Requirements for Information Management and Fiscalisation**  
https://efris.ura.go.ug/site/manualDownload/downloadManualById?id=173517733139059055&language=

📄 **EFRIS Thumbprint & Device Registration Guide**  
https://efris.ura.go.ug/site/manualDownload/downloadManualById?id=102729662704726203&language=

---

> ⚠️ **Important Notice**  
> This SDK implements the **URA EFRIS System-to-System (S2S)** integration model.  
> Proper onboarding, certificate provisioning, and device registration with URA are required before production use.

---

## Features

✅ System-to-System (S2S) API integration  
✅ Payload encryption & digital signature support  
✅ URA-compliant request/response models  
✅ Device & taxpayer authentication helpers  
✅ Timezone-safe timestamp handling (EAT / UTC)  
✅ Offline Mode Enabler compatibility  
✅ Strong typing with **Pydantic v2**  
✅ Production-grade HTTP client  

---

## Installation

```bash
pip install ura-efris-sdk
````

---

## Author

**Bartile Emmanuel**
📧 [support@paybill.dev](mailto:support@paybill.dev) | 📱 +254 757 807 150
*Lead Developer, Paybill Kenya*

📘 URA EFRIS Documentation (Paybill):
[https://paybill.ke/docs/ura-efris](https://paybill.ke/docs/ura-efris)

---

## License

MIT © 2025–2026 Paybill Kenya Limited

🇺🇬 **Supporting Digital Tax Compliance in Uganda**
🇰🇪 Proudly engineered by Paybill Kenya Limited
