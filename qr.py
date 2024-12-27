import streamlit as st
import pandas as pd

# File path to your Excel sheet
excel_path = 'Medicine_Inventory_50_Rows.xlsx'

# Function to load Excel data
@st.cache_data
def load_data():
    try:
        data = pd.read_excel(excel_path)
        return data
    except Exception as e:
        st.error(f"Error loading the file: {e}")
        return pd.DataFrame()

# Function to update the Excel sheet
def update_excel(updated_data):
    try:
        with pd.ExcelWriter(excel_path, mode='w', engine='openpyxl') as writer:
            updated_data.to_excel(writer, index=False)
        st.success("Excel file updated successfully!")
    except Exception as e:
        st.error(f"Error updating the Excel file: {e}")

# Load data
data = load_data()

# Streamlit interface
st.title("Pharmacy Inventory Management")

if not data.empty:
    st.subheader("Available Medicines")
    st.write(data[['Medicine Name', 'Supplier Name', 'Stock', 'Expiry Date', 'Price per Unit']])

    # Order Section
    st.subheader("Place an Order")
    
    # Select Supplier
    supplier_name = st.selectbox("Select Supplier Name", options=data['Supplier Name'].unique())
    
    # Filter data for the selected supplier
    supplier_data = data[data['Supplier Name'] == supplier_name]
    
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
                    "Row Index": stock_row.index[0]  # Keep track of the row index for updates
                })

        # Generate Bill
        if order_details:
            order_df = pd.DataFrame(order_details)
            st.subheader("Order Summary")
            st.write(order_df)
            total_amount = order_df['Total Price'].sum()
            st.write(f"**Total Amount: ₹{total_amount:.2f}**")

            # Confirm and Update
            if st.button("Confirm Order"):
                for order in order_details:
                    row_index = order["Row Index"]
                    quantity_ordered = order["Quantity"]

                    # Update the specific row in the dataframe
                    data.at[row_index, 'Stock'] -= quantity_ordered

                update_excel(data)
                st.success(f"Order placed and inventory updated for supplier: {supplier_name}")
