import streamlit as st
import pandas as pd
import time
import plotly.express as px

st.set_page_config(page_title="Live Sales Dashboard", layout="wide")

st.title("📊 Live Sales & Lead Performance Dashboard")

# -------------------------------------------------
# AUTO REFRESH EVERY 60 SECONDS
# -------------------------------------------------

REFRESH_TIME = 60

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > REFRESH_TIME:
    st.session_state.last_refresh = time.time()
    st.rerun()

st.caption("🔄 Auto refreshing every 60 seconds")

# -------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------

st.markdown("""
<style>

.metric-card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    color: white;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.25);
}

.metric-value {
    font-size: 28px;
    font-weight: bold;
}

.metric-label {
    font-size: 14px;
    color: #9CA3AF;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# GOOGLE SHEET CONFIG
# -------------------------------------------------

SHEET_ID = "19nCgOuOzGMkzm6TQFlx7Yv3kYd5zELJv3kRDGOwaltk"

LEADS_GID = "1242711191"
BOOKING_GID = "0"

LEADS_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={LEADS_GID}"
BOOKING_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={BOOKING_GID}"

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

@st.cache_data(ttl=60)
def load_data():
    leads = pd.read_csv(LEADS_SHEET)
    booking = pd.read_csv(BOOKING_SHEET)
    return leads, booking

# -------------------------------------------------
# LOADING ANIMATION
# -------------------------------------------------

with st.spinner("📊 Loading Business Dashboard..."):

    progress_bar = st.progress(0)

    for i in range(100):
        time.sleep(0.005)
        progress_bar.progress(i + 1)

    leads_df, booking_df = load_data()

progress_bar.empty()

st.success("✅ Business Data Loaded Successfully")

# -------------------------------------------------
# BASIC CLEANING
# -------------------------------------------------

leads_df.columns = leads_df.columns.str.strip().str.replace("\n", " ")
booking_df.columns = booking_df.columns.str.strip().str.replace("\n", " ")

if "Product" in leads_df.columns:
    leads_df["Product"] = leads_df["Product"].astype(str).str.strip()

# -------------------------------------------------
# PRODUCT RESTRICTION
# -------------------------------------------------

allowed_products = [
    "Doctor Professional Indemnity",
    "Hospital Professional Indemnity",
    "CoverPrime"
]

leads_df = leads_df[leads_df["Product"].isin(allowed_products)]

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------

st.sidebar.header("Dashboard Filters")

month_filter = st.sidebar.multiselect(
    "Lead Month",
    options=sorted(leads_df["Lead Month"].dropna().unique()),
    default=["March-2026"]
)

department_filter = st.sidebar.multiselect(
    "Department",
    options=sorted(leads_df["Department"].dropna().unique())
)

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------

filtered_df = leads_df.copy()

if month_filter:
    filtered_df = filtered_df[filtered_df["Lead Month"].isin(month_filter)]

if department_filter:
    filtered_df = filtered_df[filtered_df["Department"].isin(department_filter)]

if "Duplicacy Check" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Duplicacy Check"] == 1]

# -------------------------------------------------
# KPI CALCULATIONS
# -------------------------------------------------

doctor_pi = filtered_df[
    filtered_df["Product"] == "Doctor Professional Indemnity"
]["Lead Id"].count()

hospital_pi = filtered_df[
    filtered_df["Product"] == "Hospital Professional Indemnity"
]["Lead Id"].count()

coverprime = filtered_df[
    filtered_df["Product"] == "CoverPrime"
]["Lead Id"].count()

total_leads = filtered_df["Lead Id"].count()

# -------------------------------------------------
# KPI CARDS
# -------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{doctor_pi:,}</div>
        <div class="metric-label">Doctor PI Leads</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{hospital_pi:,}</div>
        <div class="metric-label">Hospital PI Leads</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{coverprime:,}</div>
        <div class="metric-label">CoverPrime Leads</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_leads:,}</div>
        <div class="metric-label">Total Leads</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# PRODUCT WISE LEADS CHART
# -------------------------------------------------

st.subheader("📊 Product Wise Leads")

product_leads = (
    filtered_df.groupby("Product")
    .size()
    .reset_index(name="Total Leads")
    .sort_values("Total Leads", ascending=False)
)

fig = px.bar(
    product_leads,
    x="Product",
    y="Total Leads",
    color="Product",
    text="Total Leads"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# DEPARTMENT CONTRIBUTION
# -------------------------------------------------

st.subheader("📊 Department Contribution")

dept_contribution = (
    filtered_df.groupby("Department")["Lead Id"]
    .count()
    .reset_index(name="Leads")
)

fig = px.pie(
    dept_contribution,
    names="Department",
    values="Leads"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# DAILY LEAD TREND
# -------------------------------------------------

st.subheader("📈 Daily Lead Trend")

if "Lead Date" in filtered_df.columns:

    filtered_df["Lead Date"] = pd.to_datetime(filtered_df["Lead Date"], errors="coerce")

    daily_leads = (
        filtered_df.groupby("Lead Date")["Lead Id"]
        .count()
        .reset_index()
    )

    fig = px.line(
        daily_leads,
        x="Lead Date",
        y="Lead Id",
        markers=True
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# TARGET VS ACHIEVEMENT
# -------------------------------------------------

st.subheader("🎯 Department Target vs Achievement")

department_target = {
    "Strategic Fresh": 1000,
    "Strategic Retention": 1500,
    "CRM": 450,
    "Performance Marketing": 1500,
    "Rev-PI (PM)": 2200,
    "DRA": 1850
}

dept_leads = (
    filtered_df.groupby("Department")["Lead Id"]
    .count()
    .reset_index(name="Achievement")
)

dept_leads["Target"] = dept_leads["Department"].map(department_target)

dept_leads["Achievement %"] = (
    (dept_leads["Achievement"] / dept_leads["Target"]) * 100
).round(2).astype(str) + "%"

dept_leads = dept_leads.fillna(0)

dept_leads = dept_leads[["Department", "Target", "Achievement", "Achievement %"]]

st.dataframe(dept_leads)

st.metric("Total Leads Generated", f"{total_leads:,}")

chart_df = dept_leads.set_index("Department")[["Target", "Achievement"]]

fig = px.bar(
    chart_df,
    barmode="group"
)

st.plotly_chart(fig, use_container_width=True)