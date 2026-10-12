import streamlit as st
import pandas as pd
import os


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Bespoke Billing Automation Dashboard",
    page_icon="B",
    layout="wide"
)


# ============================================================
# FILE LOCATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

LOG_FILE = os.path.join(
    BASE_DIR,
    "billing_action_log.csv"
)


# ============================================================
# LOAD BILLING HISTORY
# ============================================================

@st.cache_data(ttl=300)
def load_history():

    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()

    try:

        history = pd.read_csv(LOG_FILE)

    except Exception as e:

        st.error(
            f"Unable to read billing action log: {e}"
        )

        return pd.DataFrame()

    expected_columns = [
        "DateTime",
        "CustomerID",
        "CustomerName",
        "Outstanding",
        "Status",
        "MikroTikUsername",
        "MikroTikIP",
        "Action",
        "Result"
    ]

    # Make sure all expected columns exist
    for column in expected_columns:

        if column not in history.columns:

            history[column] = ""

    history = history[
        expected_columns
    ]

    # Replace missing values
    history = history.fillna("")

    # Remove accidental CSV header rows
    history = history[
        history["CustomerID"]
        .astype(str)
        .str.lower()
        != "customerid"
    ]

    # Convert outstanding balance
    history["Outstanding"] = pd.to_numeric(
        history["Outstanding"],
        errors="coerce"
    ).fillna(0)

    # Convert date/time
    history["DateTime"] = pd.to_datetime(
        history["DateTime"],
        errors="coerce"
    )

    # Sort newest first
    history = history.sort_values(
        "DateTime",
        ascending=False
    )

    return history


# ============================================================
# LOAD DATA
# ============================================================

history_df = load_history()


# ============================================================
# CHECK FOR DATA
# ============================================================

if history_df.empty:

    st.title(
        "Bespoke Billing Automation Dashboard"
    )

    st.warning(
        "No billing records are currently available."
    )

    st.stop()


# ============================================================
# CURRENT CUSTOMER STATUS
# ============================================================
# The latest record for each customer is used
# for the Executive Summary.

df = history_df.drop_duplicates(
    subset=["CustomerID"],
    keep="first"
).copy()


# ============================================================
# EXECUTIVE METRICS
# ============================================================

total_customers = len(df)

total_outstanding = df[
    "Outstanding"
].sum()

suspend_count = len(
    df[
        df["Status"] == "SUSPEND"
    ]
)

grace_count = len(
    df[
        df["Status"] == "GRACE_PERIOD"
    ]
)

paid_count = len(
    df[
        df["Status"] == "PAID"
    ]
)

credit_count = len(
    df[
        df["Outstanding"] < 0
    ]
)

paid_no_balance_count = len(
    df[
        (df["Status"] == "PAID") &
        (df["Outstanding"] == 0)
    ]
)

mapped_count = len(
    df[
        df["MikroTikUsername"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
    ]
)

not_mapped_count = (
    total_customers - mapped_count
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title(
    "Bespoke Billing Automation Dashboard"
)

st.subheader(
    "QuickBooks → Billing Engine → MikroTik"
)

st.caption(
    "Automated customer billing monitoring "
    "and network access management"
)


# ============================================================
# SAFETY NOTICE
# ============================================================

st.warning(
    "DRY RUN MODE: MikroTik actions are currently simulated. "
    "No customer's internet service will actually be "
    "suspended or restored."
)


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.markdown(
    "## Executive Summary"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Customers",
        total_customers
    )


with col2:

    st.metric(
        "Net Outstanding",
        f"₵{total_outstanding:,.2f}"
    )


with col3:

    st.metric(
        "Suspension Required",
        suspend_count
    )


with col4:

    st.metric(
        "Grace Period",
        grace_count
    )


col5, col6, col7, col8 = st.columns(4)


with col5:

    st.metric(
        "Paid Customers",
        paid_count
    )


with col6:

    st.metric(
        "Customers With Credit",
        credit_count
    )


with col7:

    st.metric(
        "Paid / No Balance",
        paid_no_balance_count
    )


with col8:

    st.metric(
        "MikroTik Mapped",
        mapped_count
    )


# ============================================================
# BILLING STATUS DISTRIBUTION
# ============================================================

st.markdown("---")

st.markdown(
    "## Billing Status Distribution"
)

status_counts = df[
    "Status"
].value_counts()

st.bar_chart(
    status_counts
)


# ============================================================
# MIKROTIK ACTIONS
# ============================================================

st.markdown("---")

st.markdown(
    "## MikroTik Actions"
)


mikrotik_df = df[
    df["Action"].isin(
        ["SUSPEND", "RESTORE"]
    )
][
    [
        "CustomerID",
        "CustomerName",
        "Status",
        "MikroTikUsername",
        "MikroTikIP",
        "Action",
        "Result"
    ]
].copy()


if mikrotik_df.empty:

    st.info(
        "No MikroTik actions have been recorded."
    )

else:

    mikrotik_display = mikrotik_df.rename(
        columns={
            "CustomerID": "Customer ID",
            "CustomerName": "Customer",
            "Status": "Status",
            "MikroTikUsername": "MikroTik User",
            "MikroTikIP": "IP Address",
            "Action": "Action",
            "Result": "Reason"
        }
    )

    st.dataframe(
        mikrotik_display,
        width="stretch",
        hide_index=True
    )


# ============================================================
# GRACE PERIOD CUSTOMERS
# ============================================================

st.markdown("---")

st.markdown(
    "## Grace Period Customers"
)


grace_df = df[
    df["Status"] == "GRACE_PERIOD"
][
    [
        "CustomerID",
        "CustomerName",
        "Outstanding",
        "MikroTikUsername",
        "MikroTikIP",
        "Action",
        "Result"
    ]
].copy()


if grace_df.empty:

    st.success(
        "No customers are currently "
        "in the grace period."
    )

else:

    grace_display = grace_df.copy()

    grace_display["Outstanding"] = (
        grace_display["Outstanding"].map(
            lambda x: f"₵{x:,.2f}"
        )
    )

    grace_display = grace_display.rename(
        columns={
            "CustomerID": "Customer ID",
            "CustomerName": "Customer",
            "Outstanding": "Balance",
            "MikroTikUsername": "MikroTik User",
            "MikroTikIP": "IP Address",
            "Action": "Action",
            "Result": "Reason"
        }
    )

    st.dataframe(
        grace_display,
        width="stretch",
        hide_index=True
    )


# ============================================================
# RECENT BILLING ACTIVITY
# ============================================================

st.markdown("---")

st.markdown(
    "## Recent Billing Activity"
)

st.caption(
    "Latest billing transactions recorded by the system"
)


recent_df = history_df.head(10).copy()


recent_display = recent_df.copy()


recent_display["Outstanding"] = (
    recent_display["Outstanding"].map(
        lambda x: f"₵{x:,.2f}"
    )
)


recent_display["DateTime"] = (
    recent_display["DateTime"]
    .dt.strftime("%Y-%m-%d %H:%M:%S")
)


recent_display = recent_display.rename(
    columns={
        "DateTime": "Date & Time",
        "CustomerID": "Customer ID",
        "CustomerName": "Customer",
        "Outstanding": "Balance",
        "Status": "Status",
        "Action": "Action",
        "Result": "Reason"
    }
)


st.dataframe(
    recent_display[
        [
            "Date & Time",
            "Customer ID",
            "Customer",
            "Balance",
            "Status",
            "Action",
            "Reason"
        ]
    ],
    width="stretch",
    hide_index=True
)


# ============================================================
# DOWNLOAD RECENT ACTIVITY
# ============================================================

recent_download = recent_df.copy()

recent_download["DateTime"] = (
    recent_download["DateTime"]
    .dt.strftime("%Y-%m-%d %H:%M:%S")
)


recent_csv = recent_download.to_csv(
    index=False
)


st.download_button(
    label="Download Recent Activity (CSV)",
    data=recent_csv,
    file_name="recent_billing_activity.csv",
    mime="text/csv"
)


# ============================================================
# FULL BILLING HISTORY
# ============================================================

st.markdown("---")

st.markdown(
    "## Billing History"
)

st.caption(
    f"Total billing records available: "
    f"{len(history_df)}"
)


# ============================================================
# SEARCH BILLING HISTORY
# ============================================================

search_text = st.text_input(
    "Search Billing History",
    placeholder=(
        "Search customer, Customer ID, status, "
        "action, MikroTik username, or IP address..."
    )
)


filtered_history = history_df.copy()


if search_text:

    search_text = (
        search_text
        .strip()
        .lower()
    )

    searchable_columns = [
        "CustomerID",
        "CustomerName",
        "Status",
        "MikroTikUsername",
        "MikroTikIP",
        "Action",
        "Result"
    ]

    search_mask = (
        filtered_history[
            searchable_columns
        ]
        .astype(str)
        .apply(
            lambda column:
            column
            .str
            .lower()
            .str.contains(
                search_text,
                na=False,
                regex=False
            )
        )
        .any(axis=1)
    )

    filtered_history = (
        filtered_history[
            search_mask
        ]
    )


st.caption(
    f"Showing {len(filtered_history)} "
    f"of {len(history_df)} billing records"
)


# ============================================================
# PREPARE HISTORY FOR DISPLAY
# ============================================================

history_display = (
    filtered_history.copy()
)


history_display["Outstanding"] = (
    history_display["Outstanding"].map(
        lambda x: f"₵{x:,.2f}"
    )
)


history_display["DateTime"] = (
    history_display["DateTime"]
    .dt.strftime("%Y-%m-%d %H:%M:%S")
)


history_display = history_display.rename(
    columns={
        "DateTime": "Date & Time",
        "CustomerID": "Customer ID",
        "CustomerName": "Customer",
        "Outstanding": "Balance",
        "Status": "Status",
        "MikroTikUsername": "MikroTik User",
        "MikroTikIP": "IP Address",
        "Action": "Action",
        "Result": "Reason"
    }
)


# ============================================================
# DISPLAY FULL HISTORY
# ============================================================

st.dataframe(
    history_display[
        [
            "Date & Time",
            "Customer ID",
            "Customer",
            "Balance",
            "Status",
            "MikroTik User",
            "IP Address",
            "Action",
            "Reason"
        ]
    ],
    width="stretch",
    hide_index=True,
    height=450
)


# ============================================================
# DOWNLOAD BILLING HISTORY
# ============================================================

download_df = (
    filtered_history.copy()
)


download_df["DateTime"] = (
    download_df["DateTime"]
    .dt.strftime("%Y-%m-%d %H:%M:%S")
)


download_csv = download_df.to_csv(
    index=False
)


if search_text:

    download_filename = (
        "filtered_billing_history.csv"
    )

else:

    download_filename = (
        "billing_history.csv"
    )


st.download_button(
    label="Download Billing History (CSV)",
    data=download_csv,
    file_name=download_filename,
    mime="text/csv"
)


# ============================================================
# MIKROTIK MAPPING SUMMARY
# ============================================================

st.markdown("---")

st.markdown(
    "## MikroTik Mapping Summary"
)


map_col1, map_col2 = st.columns(2)


with map_col1:

    st.metric(
        "Mapped Customers",
        mapped_count
    )


with map_col2:

    st.metric(
        "Not Mapped",
        not_mapped_count
    )


# ============================================================
# SYSTEM WORKFLOW
# ============================================================

st.markdown("---")

st.markdown(
    "## System Workflow"
)


st.info(
    "QuickBooks Online Sandbox  →  "
    "Billing Engine  →  "
    "Billing Decision  →  "
    "MikroTik"
)


st.markdown(
    "### Billing Decision Rules"
)


decision_col1, decision_col2, decision_col3 = (
    st.columns(3)
)


with decision_col1:

    st.success(
        "PAID\n\nRESTORE"
    )


with decision_col2:

    st.warning(
        "GRACE PERIOD\n\nNO ACTION"
    )


with decision_col3:

    st.error(
        "SUSPEND\n\nSUSPEND"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Bespoke Billing Automation System"
)

st.caption(
    "Management Demonstration | "
    "QuickBooks → Billing Engine → MikroTik | "
    "DRY RUN MODE"
)