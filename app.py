import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Trip Expenses", page_icon="🚗")
st.title("🚗 Trip Expense Tracker")

# Establish connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read existing data
df = conn.read(worksheet="Sheet1", usecols=[0, 1])
df = df.dropna(how="all")  # Clean up empty rows

# Calculate total
total_spent = df["Amount"].sum() if not df.empty else 0
st.metric("Total Expenses (₹)", f"₹ {total_spent:,.2f}")

# Input form
with st.form("add_expense", clear_on_submit=True):
    item = st.text_input("What for?")
    amount = st.number_input("How much? (₹)", min_value=0.0, step=10.0)
    submitted = st.form_submit_button("Add Expense")

    if submitted and item and amount > 0:
        # Create a new row
        new_row = pd.DataFrame([{"Item": item, "Amount": amount}])
        updated_df = pd.concat([df, new_row], ignore_index=True)

        # Update Google Sheet
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success(f"Added {item} successfully!")
        st.rerun()

# Display history
st.write("### Expense History")
st.dataframe(df, use_container_width=True)
