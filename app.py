import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import time

st.title("📊 A/B Chart Testing App")

# ── Business question ──────────────────────────────────────────────────────────
st.info("❓ **Business Question:** Which regions have a higher concentration of high-income households?")

# ── 1. Load dataset ────────────────────────────────────────────────────────────
@st.cache_data
def load_default():
    url = "https://cdn.jsdelivr.net/npm/vega-datasets@latest/data/income.json"
    return pd.read_json(url)

# 100% feature: allow user to upload their own dataset
st.sidebar.header("📁 Dataset Options")
uploaded = st.sidebar.file_uploader("Upload your own CSV or JSON", type=["csv", "json"])

if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_json(uploaded)
    st.sidebar.success(f"Loaded: {uploaded.name}")
else:
    df = load_default()
    st.sidebar.info("Using default: income.json")

# 100% feature: let user pick which variable to analyse
numeric_cols = df.select_dtypes(include="number").columns.tolist()
string_cols  = df.select_dtypes(include="object").columns.tolist()

group_col = st.sidebar.selectbox(
    "Group-by column (category)",
    string_cols,
    index=string_cols.index("region") if "region" in string_cols else 0
)
value_col = st.sidebar.selectbox(
    "Value column to analyse",
    numeric_cols,
    index=numeric_cols.index("pct") if "pct" in numeric_cols else 0
)

# ── 2. Filter widget (70% extra) ──────────────────────────────────────────────
if "subregion" in df.columns:
    all_subs = sorted(df["subregion"].dropna().unique().tolist())
    selected = st.sidebar.multiselect("Filter by subregion", all_subs, default=all_subs)
    if selected:
        df = df[df["subregion"].isin(selected)]

# ── 3. Chart definitions ──────────────────────────────────────────────────────
def chart_a(data, group, value):
    """Chart A – Horizontal bar chart (mean value per group)."""
    summary = (
        data.groupby(group)[value]
        .mean()
        .reset_index()
        .sort_values(value, ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=summary, y=group, x=value, palette="Blues_d", ax=ax)
    ax.set_title(f"Chart A – Mean '{value}' by {group}", fontsize=13)
    ax.set_xlabel(f"Mean {value}")
    ax.set_ylabel(group.capitalize())
    plt.tight_layout()
    return fig

def chart_b(data, group, value):
    """Chart B – Box plot showing full distribution per group."""
    order = (
        data.groupby(group)[value]
        .median()
        .sort_values(ascending=False)
        .index
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=data, x=value, y=group, order=order, palette="Oranges", ax=ax)
    ax.set_title(f"Chart B – Distribution of '{value}' by {group}", fontsize=13)
    ax.set_xlabel(value)
    ax.set_ylabel(group.capitalize())
    plt.tight_layout()
    return fig

CHARTS = {"A": chart_a, "B": chart_b}

# ── 4. Session state initialisation ───────────────────────────────────────────
for key, default in [
    ("chart_key",  None),
    ("start_time", None),
    ("results",    []),
    ("answered",   False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── 5. Random chart button ────────────────────────────────────────────────────
if st.button("🎲 Show me a random chart", use_container_width=True):
    st.session_state.chart_key  = random.choice(["A", "B"])
    st.session_state.start_time = time.time()
    st.session_state.answered   = False

if st.session_state.chart_key:
    key = st.session_state.chart_key
    fig = CHARTS[key](df, group_col, value_col)
    st.pyplot(fig)
    plt.close(fig)

    if not st.session_state.answered:
        if st.button("✅ Did this answer your question?", use_container_width=True):
            elapsed = round(time.time() - st.session_state.start_time, 2)
            st.session_state.results.append({"chart": key, "seconds": elapsed})
            st.session_state.answered = True
            st.success(f"⏱️ It took you **{elapsed} seconds** to answer using Chart {key}.")
            st.rerun()
    else:
        last = st.session_state.results[-1]
        st.success(f"⏱️ It took you **{last['seconds']} seconds** to answer using Chart {last['chart']}.")

# ── 6. Live scoreboard ────────────────────────────────────────────────────────
if st.session_state.results:
    st.divider()
    st.subheader("📈 A/B Test Results")

    res_df  = pd.DataFrame(st.session_state.results)
    summary = (
        res_df.groupby("chart")["seconds"]
        .agg(Responses="count", Avg_seconds="mean")
        .reset_index()
        .rename(columns={"chart": "Chart"})
    )
    summary["Avg_seconds"] = summary["Avg_seconds"].round(2)
    st.dataframe(summary, use_container_width=True)

    winner = summary.loc[summary["Avg_seconds"].idxmin(), "Chart"]
    st.markdown(f"🏆 **Fastest-understood chart so far: Chart {winner}**")

    if st.button("🗑️ Reset results"):
        st.session_state.results   = []
        st.session_state.chart_key = None
        st.session_state.answered  = False
        st.rerun()
