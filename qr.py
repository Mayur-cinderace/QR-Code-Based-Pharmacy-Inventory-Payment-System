import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheet URL
google_sheet_url = "https://docs.google.com/spreadsheets/d/1XEJUuvDAuWzzjKxgYhAUVi6jDxugTx0Gvn8NyvVZ1w8/edit?gid=1470509049#gid=1470509049"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def load_google_sheet(sheet_url):
    try:
        credentials_info = st.secrets["google_credentials"]
        credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_url(sheet_url)
        
        # Access the first sheet in the spreadsheet
        sheet = spreadsheet.sheet1
        data = pd.DataFrame(sheet.get_all_records())
        return spreadsheet, sheet, data
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return None, None, pd.DataFrame()

def load_payment_history(spreadsheet):
    try:
        try:
            payment_sheet = spreadsheet.worksheet("Payment History")
        except gspread.exceptions.WorksheetNotFound:
            payment_sheet = spreadsheet.add_worksheet(title="Payment History", rows="100", cols="20")
            headers = ["Medicine Name", "Quantity", "Total Price", "Supplier Name", "Payment Method", "Payment Reference", "Timestamp"]
            payment_sheet.append_row(headers)
            st.info("Created a new 'Payment History' sheet as it was missing.")

        data = pd.DataFrame(payment_sheet.get_all_records())
        return data
    except Exception as e:
        st.error(f"Error loading payment history: {e}")
        return pd.DataFrame()

def update_google_sheet(sheet, updated_data):
    try:
        sheet.clear()
        sheet.update([updated_data.columns.values.tolist()] + updated_data.values.tolist())
        st.success("Google Sheet updated successfully!")
    except Exception as e:
        st.error(f"Error updating Google Sheet: {e}")

def log_payment(spreadsheet, payment_details):
    try:
        try:
            payment_sheet = spreadsheet.worksheet("Payment History")
        except gspread.exceptions.WorksheetNotFound:
            payment_sheet = spreadsheet.add_worksheet(title="Payment History", rows="100", cols="20")
            headers = ["Medicine Name", "Quantity", "Total Price", "Supplier Name", "Payment Method", "Payment Reference", "Timestamp"]
            payment_sheet.append_row(headers)

        for detail in payment_details:
            row = [
                detail["Medicine Name"],
                detail["Quantity"],
                detail["Total Price"],
                detail["Supplier Name"],
                detail["Payment Method"],
                detail["Payment Reference"],
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]
            payment_sheet.append_row(row)

        st.success("Payment history logged successfully!")
    except Exception as e:
        st.error(f"Error logging payment history: {e}")

st.title("Pharmacy Inventory Management")

spreadsheet, sheet, data = load_google_sheet(google_sheet_url)

if not data.empty:
    st.subheader("Available Medicines")
    medicines_table = st.empty()
    medicines_table.write(data[['Medicine Name', 'Supplier Name', 'Stock', 'Expiry Date', 'Price per Unit']])

    st.subheader("Place an Order")

    supplier_name = st.selectbox("Select Supplier Name", options=data['Supplier Name'].unique())
    supplier_data = data[data['Supplier Name'] == supplier_name]
    supplier_data = supplier_data.sort_values(by='Expiry Date')

    ordered_medicines = st.multiselect("Select Medicines to Order", options=supplier_data['Medicine Name'].unique())

    if ordered_medicines:
        order_details = []
        for medicine in ordered_medicines:
            stock_row = supplier_data[supplier_data['Medicine Name'] == medicine]
            max_quantity = int(stock_row['Stock'].iloc[0])
            price_per_unit = float(stock_row['Price per Unit'].iloc[0])

            st.write(f"Available stock for {medicine} from {supplier_name}: {max_quantity}")
            quantity = st.number_input(f"Enter quantity for {medicine}", min_value=0, max_value=max_quantity, step=1)
            if quantity > 0:
                order_details.append({
                    "Medicine Name": medicine,
                    "Quantity": quantity,
                    "Price per Unit": price_per_unit,
                    "Total Price": quantity * price_per_unit,
                    "Supplier Name": supplier_name,
                    "Row Index": stock_row.index[0],
                })

        if order_details:
            order_df = pd.DataFrame(order_details)
            st.subheader("Order Summary")
            st.write(order_df)
            total_amount = order_df['Total Price'].sum()
            st.write(f"*Total Amount: ₹{total_amount:.2f}*")

            st.subheader("Payment Options")
            st.write("**Razorpay Integration Coming Soon**")

            if st.button("Confirm Order"):
                for order in order_details:
                    row_index = order["Row Index"]
                    quantity_ordered = order["Quantity"]
                    data.at[row_index, 'Stock'] -= quantity_ordered

                update_google_sheet(sheet, data)

                for detail in order_details:
                    detail["Payment Method"] = "Razorpay"
                    detail["Payment Reference"] = "Razorpay Transaction"

                log_payment(spreadsheet, order_details)
                medicines_table.write(data[['Medicine Name', 'Supplier Name', 'Stock', 'Expiry Date', 'Price per Unit']])
                st.success(f"Order placed and inventory updated for supplier: {supplier_name}")

    st.subheader("Payment History")
    try:
        payment_sheet = spreadsheet.worksheet("Payment History")
        payment_history_data = pd.DataFrame(payment_sheet.get_all_records())
        if not payment_history_data.empty:
            st.write(payment_history_data)
        else:
            st.info("No payment history found.")
    except gspread.exceptions.WorksheetNotFound:
        st.warning("Payment History sheet does not exist.")
    except Exception as e:
        st.error(f"Error loading payment history: {e}")
