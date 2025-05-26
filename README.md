# 💊 QR Code-Based Pharmacy Inventory & Payment System

This Streamlit-based web app integrates Google Sheets for managing pharmacy inventory and generates dynamic UPI QR codes for seamless payments. It supports medicine selection by supplier, stock validation, order logging, and real-time inventory updates—all connected to your Google Sheet.

## 🚀 Features
📦 Inventory Display – View real-time medicine stock from Google Sheets.
🧾 Order Placement – Select supplier, choose medicines, and specify quantity.
⚠️ Stock Validation – Prevents over-ordering or selection of out-of-stock items.
💳 Dynamic UPI QR Code Generation – Generates a QR code based on total order amount.
🧠 Google Sheets Integration – Reads and writes inventory and logs payment history.
🗂️ Payment History Tracking – Automatically logs every transaction with timestamp.

## 🧱 Tech Stack
Streamlit – UI framework
Pandas – Data manipulation
Gspread – Google Sheets API wrapper
qrcode – For generating UPI QR codes
Google Sheets API

## 📁 Project Structure
.
├── qr_app.py                # Main Streamlit application
├── requirements.txt         # Python dependencies
└── .streamlit/secrets.toml # Google API credentials (not included in repo)

## 🔧 Setup Instructions
### Clone the Repository
git clone https://github.com/Mayur-cinderace/QR-Code.git
cd QR-Code

### Create Virtual Environment & Install Dependencies
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

### Add Google Credentials
Create .streamlit/secrets.toml
[google_credentials]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
...

### Run the App
streamlit run qr_app.py

## 📦 Google Sheet Format
The Google Sheet should contain the following columns in the first sheet:

Medicine Name
Supplier Name
Stock
Expiry Date
Price per Unit
If a Payment History worksheet does not exist, the app will create it with:
Medicine Name
Quantity
Total Price
Supplier Name
Payment Method
Payment Reference
Timestamp
