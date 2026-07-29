import streamlit as st
import pandas as pd
import sqlite3
import json
import plotly.express as px
import subprocess
import sys

st.set_page_config(page_title="Data Engineering Pipeline Dashboard", layout="wide")

st.title("🔥 Data Engineering Pipeline Dashboard")
st.caption("Built by Pozhar — Weeks 4-8 combined into one live application")

# Sidebar navigation
section = st.sidebar.radio("Navigate to:", [
    "🏠 Overview",
    "📥 Week 4 — Crypto ETL",
    "✅ Week 5 — Data Quality",
    "📸 Week 6 — CDC Tracker",
    "⭐ Week 7-8 — Star Schema"
])

# ============ OVERVIEW ============
if section == "🏠 Overview":
    st.header("Pipeline Overview")
    st.markdown("""
    This dashboard combines 5 weeks of data engineering work into one live application:
    
    1. **Extract & Load** — Pull live crypto data from an API (Week 4)
    2. **Validate** — Check data quality automatically (Week 5)
    3. **Track Changes** — Monitor database changes in real-time (Week 6)
    4. **Analyze** — Query a star schema data warehouse (Week 7-8)
    
    Use the sidebar to explore each stage of the pipeline.
    """)

# ============ WEEK 4 — CRYPTO ETL ============
elif section == "📥 Week 4 — Crypto ETL":
    st.header("Crypto ETL Pipeline")
    st.markdown("Extracts live cryptocurrency prices, transforms and loads them into SQLite.")

    conn = sqlite3.connect("crypto.db")
    df = pd.read_sql("SELECT * FROM coin_prices ORDER BY ingested_at DESC LIMIT 250", conn)
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Snapshots", len(df))
    col2.metric("Unique Coins", df['id'].nunique())
    col3.metric("Last Updated", df['ingested_at'].max())

    st.subheader("Top 10 Coins by Market Cap")
    top10 = df.sort_values('market_cap', ascending=False).head(10)
    fig = px.bar(top10, x='name', y='market_cap', color='name', title="Top 10 by Market Cap")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Raw Data")
    st.dataframe(df.head(20))

# ============ WEEK 5 — DATA QUALITY ============
elif section == "✅ Week 5 — Data Quality":
    st.header("Data Quality Checks")
    st.markdown("Runs YAML-defined validation rules against the crypto dataset.")

    if st.button("Run Data Quality Checks"):
        result = subprocess.run([sys.executable, "dq.py", "coin_prices.yml"], capture_output=True, text=True)
        st.code(result.stdout, language="text")

    st.subheader("Known Issue Found")
    st.warning("🐛 Bug found: The `symbol` column contains Chinese characters (e.g. 币安人生) that fail the regex pattern `^[a-z0-9]+$`. This was caught automatically by the data quality checker.")

# ============ WEEK 6 — CDC TRACKER ============
elif section == "📸 Week 6 — CDC Tracker":
    st.header("Change Data Capture (CDC) Activity")
    st.markdown("Real-time log of INSERT, UPDATE and DELETE operations on the customers table.")

    events = []
    with open("events.jsonl") as f:
        for line in f:
            events.append(json.loads(line))

    df_events = pd.DataFrame(events)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Events", len(df_events))
    col2.metric("Inserts", len(df_events[df_events['op'] == 'INSERT']))
    col3.metric("Updates/Deletes", len(df_events[df_events['op'].isin(['UPDATE', 'DELETE'])]))

    st.subheader("Event Type Breakdown")
    op_counts = df_events['op'].value_counts().reset_index()
    op_counts.columns = ['Operation', 'Count']
    fig = px.pie(op_counts, names='Operation', values='Count', title="CDC Operations")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Events")
    st.dataframe(df_events.tail(10))

# ============ WEEK 7-8 — STAR SCHEMA ============
elif section == "⭐ Week 7-8 — Star Schema":
    st.header("GitHub Events Star Schema")
    st.markdown("Analytics on 836,573 real GitHub events loaded into a dimensional model.")

    st.info("Connect to Postgres to see live star schema data. Run: `sudo docker start pg-cdc` first.")

    try:
        import psycopg2
        conn = psycopg2.connect(host="localhost", port=5432, dbname="postgres", user="postgres", password="password")
        
        query = """
        SELECT et.event_type_name, COUNT(*) as count
        FROM fact_events fe
        JOIN dim_event_type et ON fe.event_type_sk = et.event_type_sk
        GROUP BY et.event_type_name
        ORDER BY count DESC
        """
        df_types = pd.read_sql(query, conn)
        conn.close()

        st.subheader("Event Types Distribution")
        fig = px.bar(df_types, x='event_type_name', y='count', title="GitHub Event Types")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_types)
    except Exception as e:
        st.error(f"Could not connect to Postgres. Make sure Docker is running. Error: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("BuyPower Data Engineering Internship — Week 9 Capstone")
