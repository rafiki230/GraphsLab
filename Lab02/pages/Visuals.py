
import streamlit as st
import pandas as pd
import json  
import os    


st.set_page_config(
    page_title="Visualizations",
    page_icon="📈",
)


st.title("Data Visualizations 📈")
st.write("This page displays graphs based on the collected data.")


if "selected_states" not in st.session_state:
    st.session_state["selected_states"] = []  
if "marker_size" not in st.session_state:
    st.session_state["marker_size"] = 10      
if "csv_category" not in st.session_state:
    st.session_state["csv_category"] = ""     
if "csv_min_value" not in st.session_state:
    st.session_state["csv_min_value"] = 0.0   
if "show_labels" not in st.session_state:
    st.session_state["show_labels"] = False   


st.divider()
st.header("Load Data")

csv_df = pd.DataFrame(columns=["Category", "Value"])
csv_path = "data.csv"
if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
    try:
        tmp = pd.read_csv(csv_path)

        cols = [c.strip().title() for c in tmp.columns]
        tmp.columns = cols
        if "Value" in tmp.columns:
            tmp["Value"] = pd.to_numeric(tmp["Value"], errors="coerce")
        csv_df = tmp
        st.success("Loaded data.csv successfully.")
        st.dataframe(csv_df, use_container_width=True)
    except Exception as e:
        st.error(f"Could not read data.csv: {e}")
else:
    st.warning("The 'data.csv' file is empty or does not exist yet.")

json_df = pd.DataFrame(columns=["state", "suicide_rate", "gun_ownership"])
json_path = "data.json"
if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        records = jdata.get("records", [])
        if records:
            tmp = pd.DataFrame(records)
            rename_map = {}
            for col in tmp.columns:
                if "suicide" in col:
                    rename_map[col] = "suicide_rate"
                if "gun" in col and "ownership" in col:
                    rename_map[col] = "gun_ownership"
            if rename_map:
                tmp = tmp.rename(columns=rename_map)
            for need in ["state", "suicide_rate", "gun_ownership"]:
                if need not in tmp.columns:
                    tmp[need] = pd.NA
            tmp["suicide_rate"] = pd.to_numeric(tmp["suicide_rate"], errors="coerce")
            tmp["gun_ownership"] = pd.to_numeric(tmp["gun_ownership"], errors="coerce")
            json_df = tmp[["state", "suicide_rate", "gun_ownership"]].dropna()
            st.success("Loaded data.json successfully.")
            st.dataframe(json_df, use_container_width=True)
        else:
            st.warning("data.json has no 'records' list or it is empty.")
    except Exception as e:
        st.error(f"Could not read data.json: {e}")
else:
    st.warning("The 'data.json' file is empty or does not exist yet.")


st.divider()
st.header("Graphs")


st.subheader("Graph 1: Static — Suicide Rates by State (JSON)")
if json_df.empty:
    st.warning("Placeholder for your first graph. (JSON data not available yet.)")
else:
    bar_df = json_df.dropna(subset=["state", "suicide_rate"]).set_index("state")[["suicide_rate"]]
    st.bar_chart(bar_df)
    st.caption("This static bar chart shows the suicide rate per 100,000 people for each state (from **data.json**).")


st.subheader("Graph 2: Dynamic — Suicide Rate vs. Gun Ownership (JSON)")
if json_df.empty:
    st.warning("Placeholder for your second graph. (JSON data not available yet.)")
else:
    states = json_df["state"].dropna().tolist()

    selected = st.multiselect(                
        "Select states to display:",
        options=states,
        default=st.session_state["selected_states"] or states[:]
    )
    st.session_state["selected_states"] = selected

    size = st.slider(                          
        "Adjust marker size:",
        min_value=4, max_value=24, value=st.session_state["marker_size"]
    )
    st.session_state["marker_size"] = size

    show_labels = st.checkbox(                 
        "Show data labels",
        value=st.session_state["show_labels"]
    )
    st.session_state["show_labels"] = show_labels

    # Build filtered data
    scatter_df = json_df.copy()
    if selected:
        scatter_df = scatter_df[scatter_df["state"].isin(selected)]
    scatter_df = scatter_df.dropna(subset=["suicide_rate", "gun_ownership"])
    scatter_df["marker_size"] = (scatter_df["suicide_rate"] * 0.6 + 6) * (size / 10.0)

    if scatter_df.empty:
        st.warning("No states match your current selection.")
    else:
        st.scatter_chart(
            scatter_df,
            x="gun_ownership",
            y="suicide_rate",
            size="marker_size",
            color="state"
        )
        st.caption(
            "Dynamic scatter plot showing suicide rate (y) vs. estimated household gun ownership (x). "
            "Use the multiselect to choose states and the slider to scale point sizes."
        )

        if show_labels:
            st.write("Selected points (label view):")
            st.dataframe(scatter_df[["state", "gun_ownership", "suicide_rate"]].reset_index(drop=True))

st.subheader("Graph 3: Dynamic — Category Values Over Submissions (CSV)")
if csv_df.empty:
    st.warning("Placeholder for your third graph. (CSV data not available yet; add entries on the Survey page.)")
else:
    clean = csv_df.dropna(subset=["Category"]).copy()
    clean["Value"] = pd.to_numeric(clean["Value"], errors="coerce")
    clean = clean.dropna(subset=["Value"]).reset_index(drop=True)
    clean["SubmissionIndex"] = clean.index + 1  # pseudo-time axis

    categories = sorted(clean["Category"].unique().tolist())
    if not st.session_state["csv_category"] or st.session_state["csv_category"] not in categories:
        st.session_state["csv_category"] = categories[0] if categories else ""

    picked_cat = st.selectbox(                  #NEW
        "Choose a category:",
        options=categories,
        index=categories.index(st.session_state["csv_category"]) if categories else 0
    )
    st.session_state["csv_category"] = picked_cat

    min_allowed = float(clean["Value"].min()) if not clean.empty else 0.0
    max_allowed = float(clean["Value"].max()) if not clean.empty else 100.0

    min_val = st.slider(                        #NEW
        "Minimum value filter:",
        min_value=min_allowed,
        max_value=max_allowed,
        value=float(st.session_state["csv_min_value"]) if min_allowed <= st.session_state["csv_min_value"] <= max_allowed else min_allowed
    )
    st.session_state["csv_min_value"] = float(min_val)

    view = clean[(clean["Category"] == st.session_state["csv_category"]) & (clean["Value"] >= st.session_state["csv_min_value"])]

    if view.empty:
        st.warning("No rows match your filters. Try a different category or lower the minimum value.")
    else:
        line_df = view[["SubmissionIndex", "Value"]].set_index("SubmissionIndex")
        st.line_chart(line_df)
        st.caption(
            "Dynamic line chart of CSV inputs for the selected category over submission order. "
            "Use the category dropdown and the minimum-value slider to explore your data."
        )
