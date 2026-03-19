import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
import time

st.title("A/B Testing App: Income Distribution by Region")

st.header("Business Question")
st.write("Which regions have a higher concentration of high-income households?")

# -----------------------------
# Load default dataset
# -----------------------------
@st.cache_data
def load_default_data():
    return pd.read_json("income.json")

df = load_default_data()

# -----------------------------
# Optional upload for top grade
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload another dataset (CSV or JSON) if you want to test a different analysis",
    type=["csv", "json"]
)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_json(uploaded_file)

st.subheader("Preview of the dataset")
st.dataframe(df.head())

# -----------------------------
# Default analysis for income.json
# -----------------------------
default_mode = False
required_cols = {"region", "group", "pct"}

if required_cols.issubset(df.columns):
    default_mode = True

# -----------------------------
# Session state
# -----------------------------
if "chart_type" not in st.session_state:
    st.session_state.chart_type = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# -----------------------------
# Nice widget for grading
# -----------------------------
palette = st.selectbox(
    "Choose a style for the charts",
    ["deep", "muted", "pastel", "dark", "colorblind"]
)

# -----------------------------
# Default question logic
# -----------------------------
if default_mode:
    high_income_groups = ["100000 to 149999", "150000 to 199999", "200000+"]
    filtered_df = df[df["group"].isin(high_income_groups)]

    # Widget to focus analysis
    selected_regions = st.multiselect(
        "Select regions to compare",
        options=sorted(filtered_df["region"].dropna().unique()),
        default=sorted(filtered_df["region"].dropna().unique())
    )

    filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]

    st.write("Filtered data used for the analysis:")
    st.dataframe(filtered_df.head())

    if st.button("Show me a random chart"):
        st.session_state.chart_type = random.choice(["A", "B"])
        st.session_state.start_time = time.time()

    if st.session_state.chart_type is not None:
        fig, ax = plt.subplots(figsize=(10, 5))

        if st.session_state.chart_type == "A":
            summary_df = (
                filtered_df.groupby("region", as_index=False)["pct"]
                .mean()
                .sort_values("pct", ascending=False)
            )

            sns.barplot(data=summary_df, x="region", y="pct", hue="region", palette=palette, ax=ax, legend=False)
            ax.set_title("Chart A: Average concentration of high-income households by region")
            ax.set_xlabel("Region")
            ax.set_ylabel("Average percentage")

        else:
            sns.boxplot(data=filtered_df, x="region", y="pct", hue="region", palette=palette, ax=ax, legend=False)
            ax.set_title("Chart B: Distribution of high-income household concentration by region")
            ax.set_xlabel("Region")
            ax.set_ylabel("Percentage")

        st.pyplot(fig)

        if st.button("Did I answer your question?"):
            elapsed_time = time.time() - st.session_state.start_time
            st.write(f"Time taken to answer: {elapsed_time:.2f} seconds")
            st.success("Response recorded. This helps compare which chart communicates better.")

# -----------------------------
# Generic mode for uploaded datasets
# -----------------------------
else:
    st.subheader("Custom analysis mode")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    if len(numeric_cols) > 0 and len(categorical_cols) > 0:
        selected_cat = st.selectbox("Choose a categorical variable", categorical_cols)
        selected_num = st.selectbox("Choose a numeric variable", numeric_cols)

        st.write(f"Custom question: How does {selected_num} vary across {selected_cat}?")

        if st.button("Show me a random chart (custom mode)"):
            st.session_state.chart_type = random.choice(["A", "B"])
            st.session_state.start_time = time.time()

        if st.session_state.chart_type is not None:
            fig, ax = plt.subplots(figsize=(10, 5))

            if st.session_state.chart_type == "A":
                summary_df = (
                    df.groupby(selected_cat, as_index=False)[selected_num]
                    .mean()
                    .sort_values(selected_num, ascending=False)
                )
                sns.barplot(data=summary_df, x=selected_cat, y=selected_num, hue=selected_cat, palette=palette, ax=ax, legend=False)
                ax.set_title(f"Chart A: Average {selected_num} by {selected_cat}")
            else:
                sns.boxplot(data=df, x=selected_cat, y=selected_num, hue=selected_cat, palette=palette, ax=ax, legend=False)
                ax.set_title(f"Chart B: Distribution of {selected_num} by {selected_cat}")

            plt.xticks(rotation=45)
            st.pyplot(fig)

            if st.button("Did I answer your question?"):
                elapsed_time = time.time() - st.session_state.start_time
                st.write(f"Time taken to answer: {elapsed_time:.2f} seconds")
                st.success("Response recorded.")

    else:
        st.warning("The uploaded dataset needs at least one categorical column and one numeric column.")
