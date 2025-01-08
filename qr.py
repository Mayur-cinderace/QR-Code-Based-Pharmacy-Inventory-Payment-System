import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Google Sheet URL
google_sheet_url = "https://docs.google.com/spreadsheets/d/1XEJUuvDAuWzzjKxgYhAUVi6jDxugTx0Gvn8NyvVZ1w8/edit?gid=1470509049#gid=1470509049"  # Your Google Sheet URL
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
        return spreadsheet, sheet, data  # Return all three: spreadsheet, sheet, and data
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return None, None, pd.DataFrame()

# Load Payment History
def load_payment_history(spreadsheet):
    try:
        # Attempt to open the "Payment History" sheet
        try:
            payment_sheet = spreadsheet.worksheet("Payment History")
        except gspread.exceptions.WorksheetNotFound:
            # Create the "Payment History" sheet if it doesn't exist
            payment_sheet = spreadsheet.add_worksheet(title="Payment History", rows="100", cols="20")
            headers = ["Medicine Name", "Quantity", "Total Price", "Supplier Name", "Payment Method", "Payment Reference", "Timestamp"]
            payment_sheet.append_row(headers)
            st.info("Created a new 'Payment History' sheet as it was missing.")

        # Retrieve data from the sheet
        data = pd.DataFrame(payment_sheet.get_all_records())
        return data

    except Exception as e:
        st.error(f"Error loading payment history: {e}")
        return pd.DataFrame()

# Update Google Sheet
def update_google_sheet(sheet, updated_data):
    try:
        sheet.clear()  # Clear existing data
        sheet.update([updated_data.columns.values.tolist()] + updated_data.values.tolist())
        st.success("Google Sheet updated successfully!")
    except Exception as e:
        st.error(f"Error updating Google Sheet: {e}")

# Log payment details in the Payment History sheet
def log_payment(spreadsheet, payment_details):
    try:
        # Open or create the "Payment History" sheet
        try:
            payment_sheet = spreadsheet.worksheet("Payment History")
        except gspread.exceptions.WorksheetNotFound:
            payment_sheet = spreadsheet.add_worksheet(title="Payment History", rows="100", cols="20")
            # Add headers to the new sheet
            headers = ["Medicine Name", "Quantity", "Total Price", "Supplier Name", "Payment Method", "Payment Reference", "Timestamp"]
            payment_sheet.append_row(headers)

        # Append the new payment details
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

# Streamlit interface
st.title("Pharmacy Inventory Management")

# Load data from Google Sheet initially
spreadsheet, sheet, data = load_google_sheet(google_sheet_url)

if not data.empty:
    # Display the initial inventory table
    st.subheader("Available Medicines")
    medicines_table = st.empty()  # Placeholder for the inventory table
    medicines_table.write(data[['Medicine Name', 'Supplier Name', 'Stock', 'Expiry Date', 'Price per Unit']])

    # Order Section
    st.subheader("Place an Order")

    # Select Supplier
    supplier_name = st.selectbox("Select Supplier Name", options=data['Supplier Name'].unique())

    # Filter data for the selected supplier
    supplier_data = data[data['Supplier Name'] == supplier_name]

    # Sort medicines based on expiry date (earlier expiry first)
    supplier_data = supplier_data.sort_values(by='Expiry Date')

    # Select Medicines
    ordered_medicines = st.multiselect("Select Medicines to Order", options=supplier_data['Medicine Name'].unique())

    if ordered_medicines:
        order_details = []
        for medicine in ordered_medicines:
            # Fetch stock and price for the selected supplier and medicine
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
                    "Row Index": stock_row.index[0],  # Keep track of the row index for updates
                })

        # Generate Bill
        if order_details:
            order_df = pd.DataFrame(order_details)
            st.subheader("Order Summary")
            st.write(order_df)
            total_amount = order_df['Total Price'].sum()
            st.write(f"*Total Amount: ₹{total_amount:.2f}*")

            # Payment Options
            st.subheader("Payment Options")
            payment_options = ["Manual Payment", "Razorpay"]
            selected_payment_option = st.selectbox("Choose Payment Method", payment_options)

            payment_reference = None
            if selected_payment_option == "Manual Payment":
                payment_reference = st.text_input("Enter Payment Reference (Transaction ID/UPI ID)")
                payment_amount = st.number_input("Enter Payment Amount", min_value=0.0, step=0.01)

                if st.button("Submit Payment"):
                    if payment_reference and payment_amount == total_amount:
                        st.success("Payment details submitted. Your order will be processed.")
                    else:
                        st.error("Invalid payment details. Please try again.")

            elif selected_payment_option == "Razorpay":
                st.write("Integration for Razorpay can be added here.")

            # Confirm and Update
            if st.button("Confirm Order"):
                # Update stock in the data and Google Sheet
                for order in order_details:
                    row_index = order["Row Index"]
                    quantity_ordered = order["Quantity"]

                    # Update the specific row in the dataframe
                    data.at[row_index, 'Stock'] -= quantity_ordered

                # Update the Google Sheet with the new data
                update_google_sheet(sheet, data)

                # Log payment details
                for detail in order_details:
                    detail["Payment Method"] = selected_payment_option
                    detail["Payment Reference"] = payment_reference

                log_payment(spreadsheet, order_details)

                # Update the inventory table shown in the UI
                medicines_table.write(data[['Medicine Name', 'Supplier Name', 'Stock', 'Expiry Date', 'Price per Unit']])

                st.success(f"Order placed and inventory updated for supplier: {supplier_name}")

    # Display Payment History
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
