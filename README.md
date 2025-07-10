# 🧾 VAT Submission Automation Script

This Python script automates the VAT return submission process on the [FIRS TaxPro Max Portal](https://taxpromax.firs.gov.ng) using Selenium WebDriver. It supports batch submissions for multiple users and logs the submission outcomes in a CSV file.

---

## 📌 Features

- Logs in to the TaxPro Max portal for multiple users
- Automatically navigates to pending VAT assessments
- Selects the correct currency (`NGN`)
- Clicks through the required declaration steps
- Submits the VAT schedule, even for zero VAT declarations
- Logs each submission status and reason in a timestamped CSV file

---

## 🛠️ Requirements

- Python 3.7+
- Google Chrome
- ChromeDriver (must match your installed Chrome version)

---

## 📦 Dependencies

Install required packages with:

```bash
pip install selenium
