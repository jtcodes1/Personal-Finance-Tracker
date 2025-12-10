"""
Personal Finance Tracker (Uses Streamlit)
Author: Jos Thomas

A small personal dashboard that lets me:
- log income, expenses, and savings
- see balance (income - expenses) over time
- see expenses grouped by category
- track savings growth + progress toward a goal

"""

# Imports

import os                            # Used to check if CSV file exists
from datetime import date, datetime            # Used for default transaction date
import pandas as pd                  # Data storage and manipulation
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st               # Web app framework


# Page config & theme

# Sets the main page layout and browser tab info
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💸",
    layout="centered",
)

# Injects my dark purple theme styling and animations
st.markdown(
    """
    <style>
    :root {
      --bg: #050509;
      --bg-alt: #0d0d16;
      --bg-card: #11111c;
      --accent: #4f8cff;
      --accent-soft: rgba(79, 140, 255, 0.15);
      --text-main: #f5f5f7;
      --text-muted: #a0a0b8;
      --primary-color: #4f8cff;
      --border-subtle: #24243a;
    }

    body, .stApp {
      background: radial-gradient(circle at top left, #141428 0, #050509 45%, #020208 100%);
      color: var(--text-main);
    }

    h1, h2, h3 {
      color: var(--text-main);
    }

    [data-testid="stSidebar"] {
      background-color: #050509;
      border-right: 1px solid var(--border-subtle);
    }

    .stButton>button {
      background-color: var(--accent);
      color: white;
      border-radius: 999px;
      border: none;
      padding: 0.45rem 1.2rem;
      font-weight: 600;
    }

    .stButton>button:hover {
      background-color: #6a9bff;
    }

    /* Thinner, cleaner section cards */
    .card {
      background-color: var(--bg-card);
      border-radius: 14px;
      padding: 14px 18px;
      border: 1px solid var(--border-subtle);
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.4);
      margin-bottom: 16px;
      animation: fadeIn 0.6s ease-in;
    }

    /* Subtle fade-in animation */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Thinner glowing tube separators */
    hr {
      height: 1px;
      margin: 14px 0 18px 0;
      border: none;
      background: linear-gradient(
        to right,
        transparent,
        rgba(79, 140, 255, 0.35),
        transparent
      );
      animation: glowPulse 2.5s ease-in-out infinite;
    }

    /* Soft glow pulse animation */

    @keyframes glowPulse {
      0% { opacity: 0.35; }
      50% { opacity: 0.7; }
      100% { opacity: 0.35; }
    }

    /* Makes dropdowns taller and cleaner */

    div[data-baseweb="select"] > div {
      min-height: 48px;
      font-size: 0.95rem;
    }

    /* '''Footer hover glow effect */

     div[data-testid="stMarkdownContainer"] .footer-wrapper:hover {
       color: #a371f7;
       text-shadow:
          0 0 6px rgba(163, 113, 247, 0.6),
          0 0 12px rgba(163, 113, 247, 0.4);
        cursor: default;
    }
    /* '''Smooth transitions for color, glow, and position''' */

      div[data-testid="stMarkdownContainer"] .footer-wrapper {
        transition: 
          color 0.3s ease,
          text-shadow 0.3s ease,
          transform 0.22s ease;
    }
    /* '''Subtle hover lift animation''' */

       div[data-testid="stMarkdownContainer"] .footer-wrapper:hover {
         transform: translateY(-2px);
    }






    </style>
    """,
    unsafe_allow_html=True,
)



# Settings

# CSV file used for permanent storage
DATA_FILE = "transactions.csv"

# All supported transaction categories
CATEGORIES = [
    "Work",
    "Housing",
    "Food",
    "Transportation",
    "Utilities",
    "Shopping",
    "Health",
    "Fun",
    "Savings",
    "Other",
]


# Data helpers

def empty_df():
    '''Returns a blank DataFrame with the correct columns'''
    return pd.DataFrame(
        columns=["date", "description", "category", "amount", "type"]
    )


def load_initial_data():
    '''Loads transaction history from disk (or creates a new one if missing)'''
    if not os.path.exists(DATA_FILE):
        return empty_df()

    df = pd.read_csv(DATA_FILE)

    if df.empty:
        return empty_df()
       
     # Clean and standardize data types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["type"] = df["type"].astype(str).str.lower().str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    
    # Remove corrupted rows
    df = df.dropna(subset=["date", "amount", "type"])

    return df


def save_to_csv(df: pd.DataFrame):
    '''Saves the current DataFrame to disk'''
    df.to_csv(DATA_FILE, index=False)


def add_transaction_to_state(tx_date, desc, category, amount, t_type):
    '''Adds a single transaction row into memory and into the CSV file'''
    df = st.session_state.transactions

    # Combine chosen date with current time, store as full timestamp
    now = datetime.now()
    timestamp = datetime.combine(tx_date, now.time())
    date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    t_type = t_type.lower().strip()
        
    # Convert expenses to negative values
    if t_type == "expense":
        signed_amount = -abs(amount)
    else:
        signed_amount = abs(amount)

    new_row = {
        "date": date_str,
        "description": desc,
        "category": category,
        "amount": signed_amount,
        "type": t_type,
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    st.session_state.transactions = df

    save_to_csv(df)


# Plot functions

def plot_balance_over_time(df: pd.DataFrame):
    '''Plots running net balance over time (excluding savings)'''

    # Remove savings rows from balance calculation
    bal_df = df[df["type"] != "savings"].copy()

    if bal_df.empty:
        st.warning("No balance data yet.")
        return
    
    # Sort by date and calculate cumulative balance
    bal_df = bal_df.sort_values("date")
    bal_df["balance"] = bal_df["amount"].cumsum()
    
    # Create line plot
    fig, ax = plt.subplots()
    ax.plot(bal_df["date"], bal_df["balance"], marker="o", color="#3a7cb3")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    fig.autofmt_xdate()

    ax.set_title("Net Balance Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Balance ($)")
    ax.grid(True)
    fig.tight_layout()
    st.pyplot(fig)


def plot_expenses_by_category(df: pd.DataFrame):
    '''Plots total spending grouped by category'''

    exp_df = df[df["type"] == "expense"].copy()

    if exp_df.empty:
        st.warning("No expense data yet.")
        return
    
    # Group and total expenses by category
    totals = exp_df.groupby("category")["amount"].sum().abs().sort_values(ascending=False)

    fig, ax = plt.subplots()
    ax.bar(totals.index, totals.values, color="#3a7cb3")
    
    # Display dollar values above bars
    for i, val in enumerate(totals.values):
        ax.text(i, val + 3, f"${val:.0f}", ha="center", fontsize=10)

    ax.set_title("Spending by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount Spent ($)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    st.pyplot(fig)


def plot_savings_over_time(df: pd.DataFrame):
    '''Plots cumulative savings over time'''

    sav_df = df[df["type"] == "savings"].copy()

    if sav_df.empty:
        st.warning("No savings data yet.")
        return

    sav_df = sav_df.sort_values("date")
    sav_df["total_saved"] = sav_df["amount"].cumsum()

    fig, ax = plt.subplots()
    ax.plot(sav_df["date"], sav_df["total_saved"], marker="o", color="#3a7cb3")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    fig.autofmt_xdate()

    ax.set_title("Savings Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Saved ($)")
    ax.grid(True)
    fig.tight_layout()
    st.pyplot(fig)


# Main App

def main():
    '''Main Streamlit app controller. 
       Handles UI layout, filters, metrics, inputs, charts, and display logic.
    '''
    
    # Initialize session state storage
    if "transactions" not in st.session_state:
        st.session_state.transactions = load_initial_data()

    df = st.session_state.transactions
    filtered_df = df.copy()
    
    # App Header
    st.title("Personal Finance Tracker")
    st.caption(
        "Log income, expenses, and savings in one place and get a quick visual overview of your money. "
        "All data is stored locally in a CSV file."
    )

    # Date filter section

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Filters")

    if not df.empty:
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()

        show_all = st.checkbox("Show all time", value=True)

        if show_all:
            filtered_df = df.copy()
            st.caption("Showing all transactions.")
        else:
            col_from, col_to = st.columns(2)
            with col_from:
                start_date = st.date_input("From", value=min_date)
            with col_to:
                end_date = st.date_input("To", value=max_date)

            mask = (df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))
            filtered_df = df[mask].copy()

            st.caption(f"Showing transactions from {start_date} to {end_date}.")
    else:
        st.caption("No transactions yet.")

    st.markdown("</div>", unsafe_allow_html=True)


    # Summary metrics section

    if filtered_df.empty:
        total_income = total_expenses = total_savings = current_balance = 0.0
    else:
        total_income = filtered_df[filtered_df["type"] == "income"]["amount"].sum()
        total_expenses = -filtered_df[filtered_df["type"] == "expense"]["amount"].sum()
        total_savings = filtered_df[filtered_df["type"] == "savings"]["amount"].sum()
        current_balance = filtered_df[filtered_df["type"] != "savings"]["amount"].sum()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    left, col1, col2, col3, col4 = st.columns([0.3, 1, 1, 1, 1])


    col1.metric("Total income", f"${total_income:,.0f}")
    col2.metric("Total expenses", f"${total_expenses:,.0f}")
    col3.metric("Savings", f"${total_savings:,.0f}")
    col4.metric("Net balance", f"${current_balance:,.0f}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Sidebar input form

    with st.sidebar.form("tx_form", clear_on_submit=True):
        #Form that collects and submits new transaction data
        
        st.subheader("Add a new transaction")

        tx_date = st.date_input("Date", value=date.today())
        desc = st.text_input("Description", value="Paycheck")

        category = st.selectbox("Category", CATEGORIES)
        t_type = st.selectbox("Transaction type", ["income", "expense", "savings"])

        amount = st.number_input("Amount (USD)", min_value=0.00, step=1.0)
        submitted = st.form_submit_button("Save transaction")

        if submitted:
            add_transaction_to_state(tx_date, desc, category, amount, t_type)
            st.success("Transaction added.")
            st.rerun()


    # Transaction table

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Transaction history")

    if filtered_df.empty:
        st.info("No transactions yet. Add one in the sidebar to get started.")
    else:
        st.dataframe(filtered_df.sort_values("date", ascending=False))

        col_dl, col_reset = st.columns(2)

        with col_dl:
            st.download_button(
                "Download CSV",
                data=filtered_df.to_csv(index=False),
                file_name="transactions.csv",
                mime="text/csv",
            )

        with col_reset:
            if st.button("Clear all data"):
                st.session_state.transactions = empty_df()
                save_to_csv(st.session_state.transactions)
                st.warning("All transactions cleared.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Balance plot

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Net balance over time")
    plot_balance_over_time(filtered_df)
    st.markdown("</div>", unsafe_allow_html=True)

    # Expense plot

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Spending by category")
    plot_expenses_by_category(filtered_df)
    st.markdown("</div>", unsafe_allow_html=True)

    # Savings goal section

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Savings goal")

    goal = st.number_input("Savings goal (USD)", min_value=0.0, step=100.0, value=1000.0)
    current_saved = filtered_df[filtered_df["type"] == "savings"]["amount"].sum() if not filtered_df.empty else 0.0

    progress = 0.0 if goal <= 0 else min(current_saved / goal, 1.0)
    st.progress(progress)
    st.text(f"Saved ${current_saved:,.0f} of ${goal:,.0f} ({progress*100:.0f}%).")

    st.markdown("</div>", unsafe_allow_html=True)
    
    # Savings Growth Plot
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Savings growth over time")
    plot_savings_over_time(filtered_df)
    st.markdown("</div>", unsafe_allow_html=True)

    # Footer

    st.markdown(
        """
        <hr>
        <div class="footer-wrapper" style="text-align:center; font-size:0.85rem; margin-top:20px;">
            © 2025 Jos Thomas. Built with Python, Streamlit, pandas, and Matplotlib.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
