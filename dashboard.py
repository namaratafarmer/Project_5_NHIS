"""
TellCo Telecom — User Analytics Dashboard
Run with:  streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(page_title="TellCo Analytics", page_icon="📶", layout="wide")

# ------------------------------------------------------------
# Load data (cached so it's fast)
# ------------------------------------------------------------
@st.cache_data
def load_data():
    user = pd.read_csv("user_aggregate_labeled.csv")
    exp = pd.read_csv("experience_aggregate_labeled.csv")
    scores = pd.read_csv("final_scores.csv")
    return user, exp, scores

try:
    user_agg, exp_agg, scores = load_data()
except Exception as e:
    st.error(f"Could not load data files. Make sure the CSVs are in the same folder as this script. Error: {e}")
    st.stop()

# ------------------------------------------------------------
# Sidebar navigation
# ------------------------------------------------------------
st.sidebar.title("📶 TellCo Analytics")
st.sidebar.markdown("User Analytics for the acquisition decision")
page = st.sidebar.radio(
    "Go to section:",
    ["🏠 Overview", "👥 Engagement", "📡 Experience", "😊 Satisfaction"]
)
st.sidebar.markdown("---")
st.sidebar.caption("Prepared by Namrata Farmer\nfor NextHikes IT Solutions")

# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================
if page == "🏠 Overview":
    st.title("TellCo Telecom — User Analytics")
    st.markdown("Customer behaviour, engagement, experience & satisfaction analysis")

    # key metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", f"{len(user_agg):,}")
    c2.metric("Avg Sessions", f"{user_agg['num_xdr_sessions'].mean():.1f}")
    total_gb = user_agg["total_data_bytes"].sum() / 1e9
    c3.metric("Total Data (GB)", f"{total_gb:,.0f}")
    c4.metric("Avg Data / User (MB)", f"{user_agg['total_data_bytes'].mean()/1e6:.0f}")

    st.markdown("---")
    st.subheader("Key Findings")
    st.markdown("""
    - **Hidden fixed-wireless segment:** the most-used device is a Huawei home router, not a phone —
      TellCo has a significant home-broadband business.
    - **Device doesn't drive behaviour:** data usage is near-identical across all handset brands.
    - **One engagement dimension:** PCA shows 71% of app-usage variance is a single "overall usage" factor.
    - **Gaming dominates:** gaming (plus unclassified "Other") is ~94% of application traffic.
    """)

    # app traffic chart (if columns exist)
    app_cols = ["social_media_total", "google_total", "email_total",
                "youtube_total", "netflix_total", "gaming_total", "other_total"]
    if all(c in user_agg.columns for c in app_cols):
        st.subheader("Application Traffic (Total)")
        totals = user_agg[app_cols].sum().sort_values(ascending=False) / 1e12
        totals.index = [c.replace("_total", "").replace("_", " ").title() for c in totals.index]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(totals.index, totals.values, color="#1C7293")
        ax.set_ylabel("Traffic (Trillion Bytes)")
        ax.set_title("Total traffic by application")
        plt.xticks(rotation=30, ha="right")
        st.pyplot(fig)

# ============================================================
# PAGE 2 — ENGAGEMENT
# ============================================================
elif page == "👥 Engagement":
    st.title("👥 User Engagement Analysis")

    if "engagement_level" in user_agg.columns:
        counts = user_agg["engagement_level"].value_counts()
        order = ["Low", "Medium", "High"]
        counts = counts.reindex([o for o in order if o in counts.index])

        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Engagement Tiers")
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%",
                   colors=["#CADCFC", "#1C7293", "#065A82"], startangle=90)
            ax.axis("equal")
            st.pyplot(fig)
        with c2:
            st.subheader("Customers per Tier")
            for tier in counts.index:
                pct = counts[tier] / counts.sum() * 100
                st.metric(f"{tier} engagement", f"{counts[tier]:,}", f"{pct:.1f}% of base")

        st.markdown("---")
        st.subheader("Average Metrics per Tier")
        eng_cols = ["num_xdr_sessions", "total_duration_s", "total_data_bytes"]
        prof = user_agg.groupby("engagement_level")[eng_cols].mean().reindex(counts.index)
        prof.columns = ["Avg Sessions", "Avg Duration (s)", "Avg Data (Bytes)"]
        st.dataframe(prof.style.format("{:,.0f}"), use_container_width=True)
    else:
        st.warning("engagement_level column not found in the data.")

    # top customers
    st.markdown("---")
    st.subheader("Top 10 Customers by Total Data")
    top = user_agg.nlargest(10, "total_data_bytes")[["MSISDN/Number", "num_xdr_sessions", "total_data_bytes"]]
    top.columns = ["Customer (MSISDN)", "Sessions", "Total Data (Bytes)"]
    st.dataframe(top.style.format({"Total Data (Bytes)": "{:,.0f}", "Sessions": "{:.0f}"}), use_container_width=True)

# ============================================================
# PAGE 3 — EXPERIENCE
# ============================================================
elif page == "📡 Experience":
    st.title("📡 User Experience Analysis")

    c1, c2, c3 = st.columns(3)
    c1.metric("Median Throughput (kbps)", f"{exp_agg['avg_throughput'].median():.0f}")
    c2.metric("Median RTT (ms)", f"{exp_agg['avg_rtt'].median():.0f}")
    c3.metric("Median TCP Retrans", f"{exp_agg['avg_tcp_retrans'].median():.0f}")

    st.markdown("---")
    st.subheader("Throughput Distribution (log scale)")
    st.caption("Bimodal — low-speed phone users vs high-speed fixed-wireless (router) users")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(np.log1p(exp_agg["avg_throughput"]), bins=50, color="#55A868", edgecolor="white")
    ax.set_xlabel("log(throughput)")
    ax.set_ylabel("Customers")
    st.pyplot(fig)

    # throughput per handset
    if "handset_type" in exp_agg.columns:
        st.markdown("---")
        st.subheader("Median Throughput by Top Handset")
        top_dev = exp_agg["handset_type"].value_counts().drop("Unknown", errors="ignore").head(8).index
        sub = exp_agg[exp_agg["handset_type"].isin(top_dev)]
        tp = sub.groupby("handset_type")["avg_throughput"].median().sort_values()
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.barh(tp.index, tp.values, color="#065A82")
        ax.set_xlabel("Median throughput (kbps)")
        st.pyplot(fig)
        st.caption("The Huawei router delivers ~300× the throughput of phones — the two-tier network.")

# ============================================================
# PAGE 4 — SATISFACTION
# ============================================================
elif page == "😊 Satisfaction":
    st.title("😊 User Satisfaction Analysis")

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Satisfaction", f"{scores['satisfaction_score'].mean():.2f}")
    c2.metric("Avg Engagement", f"{scores['engagement_score'].mean():.2f}")
    c3.metric("Avg Experience", f"{scores['experience_score'].mean():.2f}")

    st.markdown("---")
    st.subheader("Top 10 Most Satisfied Customers")
    top = scores.nlargest(10, "satisfaction_score")
    show_cols = [c for c in ["msisdn", "engagement_score", "experience_score", "satisfaction_score"] if c in top.columns]
    st.dataframe(top[show_cols].style.format({c: "{:.2f}" for c in show_cols if c != "msisdn"}),
                 use_container_width=True)

    st.markdown("---")
    st.subheader("Satisfaction Score Distribution")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(scores["satisfaction_score"], bins=50, color="#F97362", edgecolor="white")
    ax.set_xlabel("Satisfaction score")
    ax.set_ylabel("Customers")
    st.pyplot(fig)

    st.info("Satisfaction is driven mainly by engagement and throughput. "
            "Improving network speed is the highest-impact lever for raising satisfaction.")
