import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Trip Expenses", page_icon="🚗", layout="centered")

# Custom CSS for better mobile experience
st.markdown("""
<style>
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
    }
    .stMetric label {
        color: #e0e0e0 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 2rem !important;
    }
    div[data-testid="stForm"] {
        border: 2px solid #667eea;
        border-radius: 15px;
        padding: 20px;
    }
    .expense-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 6px 0;
        border-left: 4px solid #667eea;
    }
    .expense-item {
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff;
    }
    .expense-details {
        font-size: 0.85rem;
        color: #a0a0a0;
    }
    .expense-amount {
        font-size: 1.1rem;
        font-weight: 700;
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# --- CATEGORY CONFIG ---
CATEGORIES = {
    "🍔 Food": "#FF6B6B",
    "⛽ Fuel": "#FFA94D",
    "🏨 Stay": "#51CF66",
    "🎟️ Tickets": "#339AF0",
    "🛍️ Shopping": "#CC5DE8",
    "🚕 Transport": "#20C997",
    "💊 Medical": "#FF8787",
    "📱 Recharge": "#748FFC",
    "🎉 Fun": "#F06595",
    "📦 Other": "#868E96",
}

# --- HEADER ---
st.title("🚗 Trip Expense Tracker")

# --- CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- READ DATA (ttl=0 forces fresh read every time, no caching) ---
df = conn.read(worksheet="Sheet1", usecols=list(range(4)), ttl=0)
df = df.dropna(how="all")

# Ensure correct columns exist
expected_cols = ["Item", "Amount", "Category", "Date"]
if df.empty:
    df = pd.DataFrame(columns=expected_cols)
else:
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

# Clean data types
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
df["Date"] = df["Date"].astype(str)

# Reset index to avoid issues
df = df.reset_index(drop=True)

# --- METRICS ROW ---
total_spent = df["Amount"].sum()
num_expenses = len(df)
avg_expense = total_spent / num_expenses if num_expenses > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Total Spent", f"₹ {total_spent:,.2f}")
with col2:
    st.metric("📊 Expenses", f"{num_expenses}")
with col3:
    st.metric("📈 Average", f"₹ {avg_expense:,.0f}")

# --- CATEGORY BREAKDOWN ---
if not df.empty and "Category" in df.columns:
    cat_data = df[df["Category"].astype(str).str.strip() != ""]
    if not cat_data.empty:
        st.markdown("---")
        st.subheader("📂 Spending by Category")
        
        category_totals = cat_data.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        
        for cat, amount in category_totals.items():
            percentage = (amount / total_spent * 100) if total_spent > 0 else 0
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.progress(min(percentage / 100, 1.0), text=f"{cat}")
            with col_b:
                st.write(f"**₹{amount:,.0f}** ({percentage:.0f}%)")

# --- ADD EXPENSE FORM ---
st.markdown("---")
st.subheader("➕ Add New Expense")

with st.form("add_expense", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        item = st.text_input("📝 What for?", placeholder="e.g., Lunch at restaurant")
    with col2:
        amount = st.number_input("💵 How much? (₹)", min_value=0.0, step=10.0, format="%.2f")
    
    col3, col4 = st.columns(2)
    
    with col3:
        category = st.selectbox("📂 Category", list(CATEGORIES.keys()))
    with col4:
        expense_date = st.date_input("📅 Date", value=date.today())
    
    submitted = st.form_submit_button("✅ Add Expense", use_container_width=True)
    
    if submitted:
        if not item:
            st.error("⚠️ Please enter what the expense is for!")
        elif amount <= 0:
            st.error("⚠️ Amount must be greater than zero!")
        else:
            # Create new row and append to existing data
            new_row = pd.DataFrame([{
                "Item": item,
                "Amount": amount,
                "Category": category,
                "Date": expense_date.strftime("%Y-%m-%d"),
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # Write ALL data back to sheet (header + all rows)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.cache_data.clear()
            st.success(f"✅ Added **{item}** — ₹{amount:,.2f}")
            st.balloons()
            st.rerun()

# --- EXPENSE HISTORY ---
st.markdown("---")
st.subheader("📜 Expense History")

if df.empty:
    st.info("No expenses yet! Add your first expense above. 👆")
else:
    # Search and filter
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search = st.text_input("🔍 Search expenses", placeholder="Type to search...")
    with col_filter:
        filter_cat = st.selectbox("Filter by category", ["All"] + list(CATEGORIES.keys()))
    
    filtered_df = df.copy()
    
    if search:
        filtered_df = filtered_df[
            filtered_df["Item"].astype(str).str.contains(search, case=False, na=False)
        ]
    if filter_cat != "All":
        filtered_df = filtered_df[filtered_df["Category"] == filter_cat]
    
    # Sort newest first
    filtered_df = filtered_df.iloc[::-1]
    
    if filtered_df.empty:
        st.warning("No expenses match your search/filter.")
    else:
        # Display as styled cards
        for idx, row in filtered_df.iterrows():
            cat_display = row.get("Category", "")
            date_display = row.get("Date", "")
            st.markdown(f"""
            <div class="expense-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="expense-item">{row['Item']}</div>
                        <div class="expense-details">{cat_display} &nbsp;•&nbsp; {date_display}</div>
                    </div>
                    <div class="expense-amount">₹ {row['Amount']:,.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.caption(f"Showing {len(filtered_df)} of {len(df)} expenses")

    # --- DELETE EXPENSE ---
    st.markdown("---")
    with st.expander("🗑️ Delete an Expense"):
        st.warning("⚠️ This action cannot be undone!")
        
        delete_options = []
        for idx, row in df.iterrows():
            label = f"#{idx + 1} — {row['Item']} — ₹{row['Amount']:,.2f} ({row.get('Date', 'N/A')})"
            delete_options.append(label)
        
        selected = st.selectbox("Select expense to delete", delete_options)
        
        if st.button("🗑️ Delete Selected", type="primary"):
            selected_idx = delete_options.index(selected)
            updated_df = df.drop(index=selected_idx).reset_index(drop=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.cache_data.clear()
            st.success("Expense deleted!")
            st.rerun()

# --- FOOTER ---
st.markdown("---")
st.caption("🚗 Trip Expense Tracker • Data synced with Google Sheets")
