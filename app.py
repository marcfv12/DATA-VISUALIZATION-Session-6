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

if "responses" not in st.session_state:
    st.session_state.responses = []

# -----------------------------
# Nice widgets
# -----------------------------
palette = st.selectbox(
    "Choose a style for the charts",
    ["deep", "muted", "pastel", "dark", "colorblind"]
)

show_data = st.checkbox("Show filtered data preview", value=True)

# -----------------------------
# Default question logic
# -----------------------------
if default_mode:
    high_income_groups = ["100000 to 149999", "150000 to 199999", "200000+"]

    selected_groups = st.multiselect(
        "Select high-income groups",
        options=high_income_groups,
        default=high_income_groups
    )

    filtered_df = df[df["group"].isin(selected_groups)]

    selected_regions = st.multiselect(
        "Select regions to compare",
        options=sorted(filtered_df["region"].dropna().unique()),
        default=sorted(filtered_df["region"].dropna().unique())
    )

    filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]

    if show_data:
        st.write("Filtered data used for the analysis:")
        st.dataframe(filtered_df.head())

    # Summary for charts
    summary_df = (
        filtered_df.groupby("region", as_index=False)["pct"]
        .sum()
        .sort_values("pct", ascending=False)
    )

    correct_region = summary_df.iloc[0]["region"]

    if st.button("Show me a random chart"):
        st.session_state.chart_type = random.choice(["A", "B"])
        st.session_state.start_time = time.time()

    if st.session_state.chart_type is not None:
        fig, ax = plt.subplots(figsize=(10, 5))

        # Chart A: vertical barplot
        if st.session_state.chart_type == "A":
            sns.barplot(
                data=summary_df,
                x="region",
                y="pct",
                hue="region",
                palette=palette,
                ax=ax,
                legend=False
            )
            ax.set_title("Chart A: High-income concentration by region")
            ax.set_xlabel("Region")
            ax.set_ylabel("Total percentage")

        # ✅ Chart B: pointplot (ONLY CHANGE)
        else:
            sns.pointplot(
                data=summary_df,
                x="region",
                y="pct",
                color="black",
                ax=ax
            )
            ax.set_title("Chart B: High-income concentration by region (dot plot)")
            ax.set_xlabel("Region")
            ax.set_ylabel("Total percentage")

        st.pyplot(fig)

        st.subheader("A/B Test Question")
        user_answer = st.radio(
            "Which region has the highest concentration of high-income households?",
            options=summary_df["region"].tolist()
        )

        confidence = st.slider(
            "How confident are you in your answer?",
            min_value=1,
            max_value=5,
            value=3
        )

        if st.button("Submit answer"):
            elapsed_time = time.time() - st.session_state.start_time
            is_correct = user_answer == correct_region

            st.session_state.responses.append({
                "chart": st.session_state.chart_type,
                "selected_region": user_answer,
                "correct_region": correct_region,
                "is_correct": is_correct,
                "response_time_sec": round(elapsed_time, 2),
                "confidence": confidence
            })

            if is_correct:
                st.success("Correct answer!")
            else:
                st.error(f"Incorrect. The correct answer is: {correct_region}")

    # -----------------------------
    # Results section
    # -----------------------------
    if len(st.session_state.responses) > 0:
        st.subheader("A/B Test Results")

        results_df = pd.DataFrame(st.session_state.responses)
        st.dataframe(results_df)

        summary_results = results_df.groupby("chart").agg(
            total_responses=("chart", "count"),
            accuracy=("is_correct", "mean"),
            avg_response_time=("response_time_sec", "mean"),
            avg_confidence=("confidence", "mean")
        ).reset_index()

        st.write("Summary by chart:")
        st.dataframe(summary_results)

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

        summary_df = (
            df.groupby(selected_cat, as_index=False)[selected_num]
            .mean()
            .sort_values(selected_num, ascending=False)
        )

        correct_category = summary_df.iloc[0][selected_cat]

        if st.button("Show me a random chart (custom mode)"):
            st.session_state.chart_type = random.choice(["A", "B"])
            st.session_state.start_time = time.time()

        if st.session_state.chart_type is not None:
            fig, ax = plt.subplots(figsize=(10, 5))

            if st.session_state.chart_type == "A":
                sns.barplot(
                    data=summary_df,
                    x=selected_cat,
                    y=selected_num,
                    hue=selected_cat,
                    palette=palette,
                    ax=ax,
                    legend=False
                )
                ax.set_title(f"Chart A: Average {selected_num} by {selected_cat}")
                plt.xticks(rotation=45)

            else:
                sns.pointplot(
                    data=summary_df,
                    x=selected_cat,
                    y=selected_num,
                    color="black",
                    ax=ax
                )
                ax.set_title(f"Chart B: Average {selected_num} by {selected_cat}")

            st.pyplot(fig)

            user_answer = st.radio(
                f"Which {selected_cat} has the highest {selected_num}?",
                options=summary_df[selected_cat].tolist(),
                key="custom_answer"
            )

            confidence = st.slider(
                "How confident are you in your answer?",
                min_value=1,
                max_value=5,
                value=3,
                key="custom_confidence"
            )

            if st.button("Submit answer (custom mode)"):
                elapsed_time = time.time() - st.session_state.start_time
                is_correct = user_answer == correct_category

                st.session_state.responses.append({
                    "chart": st.session_state.chart_type,
                    "selected_option": user_answer,
                    "correct_option": correct_category,
                    "is_correct": is_correct,
                    "response_time_sec": round(elapsed_time, 2),
                    "confidence": confidence
                })

                if is_correct:
                    st.success("Correct answer!")
                else:
                    st.error(f"Incorrect. The correct answer is: {correct_category}")

    else:
        st.warning("The uploaded dataset needs at least one categorical column and one numeric column.")
