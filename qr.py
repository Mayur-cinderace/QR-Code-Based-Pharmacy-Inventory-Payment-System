import streamlit as st
import pandas as pd

# File path to your Excel sheet
excel_path = 'Medicine_Inventory_50_Rows.xlsx'

# Load Excel data
@st.cache_data
def load_data():
    return pd.read_excel(excel_path)

# Function to update the Excel sheet
def update_excel(updated_data):
    with pd.ExcelWriter(excel_path, mode='w', engine='openpyxl') as writer:
        updated_data.to_excel(writer, index=False)

# Load the Excel sheet data
data = load_data()

# Streamlit interface
st.title("Pharmacy Inventory Management")

# Search for a medicine
st.sidebar.header("Search and Filter")
search_term = st.sidebar.text_input("Search Medicine Name")
filtered_data = data[data['Medicine Name'].str.contains(search_term, case=False, na=False)] if search_term else data

# Filter by Supplier
supplier_filter = st.sidebar.selectbox("Filter by Supplier", options=["All"] + list(data['Supplier Name'].unique()))
if supplier_filter != "All":
    filtered_data = filtered_data[filtered_data['Supplier Name'] == supplier_filter]

# Display filtered data
st.subheader("Inventory")
st.write(filtered_data)

# Reorder alert
st.subheader("Reorder Alerts")
reorder_alerts = data[data['Stock'] <= data['Reorder Level']]
if reorder_alerts.empty:
    st.success("No medicines need reordering!")
else:
    st.warning("The following medicines need reordering:")
    st.write(reorder_alerts)

# Update Stock and Expiry
st.subheader("Update Medicine Details")
medicine_to_update = st.selectbox("Select Medicine to Update", data['Medicine Name'])
new_stock = st.number_input("Enter New Stock", min_value=0, value=int(data.loc[data['Medicine Name'] == medicine_to_update, 'Stock'].values[0]))
new_expiry = st.date_input("Enter New Expiry Date", value=pd.to_datetime(data.loc[data['Medicine Name'] == medicine_to_update, 'Expiry'].values[0]))

if st.button("Update Details"):
    data.loc[data['Medicine Name'] == medicine_to_update, 'Stock'] = new_stock
    data.loc[data['Medicine Name'] == medicine_to_update, 'Expiry'] = new_expiry
    update_excel(data)
    st.success(f"{medicine_to_update} updated successfully!")

# Batch Tracking
st.subheader("Batch Information")
batch_to_view = st.selectbox("Select Batch Number", data['Batch Number'].unique())
st.write(data[data['Batch Number'] == batch_to_view])

# Optionally display the entire dataset
if st.checkbox("Show Full Data"):
    st.dataframe(data)
