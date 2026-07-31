import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="PMB Oncology Explorer",
    page_icon="🩺",
    layout="wide"
)

# -----------------------------
# Load Data
# -----------------------------
df = pd.read_csv("data/oncology_regimens.csv")

# -----------------------------
# Header
# -----------------------------
st.title("🩺 PMB Oncology Explorer")

st.markdown("""
### Interactive Decision-Support Dashboard

Explore oncology treatment costs, survival outcomes, and Prescribed Minimum Benefit (PMB) eligibility.

---

**About this dashboard**

This dashboard is based on published oncology research and has been developed as an interactive decision-support visualisation.

**Original paper:**  
https://www.linkedin.com/feed/update/urn:li:activity:7484628307024568320/

*Disclaimer:*  
All clinical analyses, methodology, and recommendations belong to the original authors. This application is an independent educational visualisation of the published findings and does not claim ownership of the underlying research.
""")

st.divider()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Filters")

condition = st.sidebar.selectbox(
    "Cancer Type",
    ["All"] + sorted(df["Condition"].unique().tolist())
)

status = st.sidebar.selectbox(
    "PMB Status",
    ["All"] + sorted(df["PMB Status"].unique().tolist())
)

# -----------------------------
# Maximum Cost Filter
# -----------------------------
max_cost = st.sidebar.slider(
    "Maximum Treatment Cost Displayed (R)",
    min_value=0,
    max_value=int(df["Cost"].max()),
    value=int(df["Cost"].max()),
    step=50000
)



filtered = df.copy()


if condition != "All":
    filtered = filtered[filtered["Condition"] == condition]



if status != "All":
    filtered = filtered[filtered["PMB Status"] == status]








colour_map = {
    "Meets": "green",
    "Fails": "red",
    "Evidence Pending": "orange"
}

print(df["PMB Status"].value_counts())
print(filtered["PMB Status"].value_counts())
# -----------------------------
# Policy Scenario Analysis
# -----------------------------


# -----------------------------
# KPI Cards
# -----------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Treatments", len(filtered))
c2.metric("Cancer Types", filtered["Condition"].nunique())
c3.metric("Average Survival", f"{filtered['OS'].mean():.1f}%")
c4.metric("Average Cost", f"R{filtered['Cost'].mean():,.0f}")


# -----------------------------
# PMB Status Summary
# -----------------------------
meets = (filtered["PMB Status"] == "Meets").sum()
fails = (filtered["PMB Status"] == "Fails").sum()
pending = (filtered["PMB Status"] == "Evidence Pending").sum()



st.divider()






most_expensive = filtered.loc[filtered["Cost"].idxmax()]
cheapest = filtered.loc[filtered["Cost"].idxmin()]
highest_survival = filtered.loc[filtered["OS"].idxmax()]

cost_ratio = most_expensive["Cost"] / cheapest["Cost"]

meets = (filtered["PMB Status"] == "Meets").sum()
fails = (filtered["PMB Status"] == "Fails").sum()
pending = (filtered["PMB Status"] == "Evidence Pending").sum()

pending_pct = (pending / len(filtered)) * 100



# -----------------------------
# Average Cost by PMB Status
# -----------------------------
status_counts = (
    filtered["PMB Status"]
    .value_counts()
    .rename_axis("PMB Status")
    .reset_index(name="Count")
)

st.subheader("📊 PMB Status Distribution")

fig = px.bar(
    status_counts,
    x="PMB Status",
    y="Count",
    color="PMB Status",
    color_discrete_map=colour_map,
    text="Count"
)

fig.update_layout(showlegend=False)

st.plotly_chart(fig, use_container_width=True)
# -------
# ----------------------
# ----------------------
# Scatter Plot
# -----------------------------

scatter_data = filtered[
    (filtered["Cost"] <= max_cost) &
    (filtered["Cost"].notna())
]

fig = px.scatter(
    scatter_data,
    x="Cost",
    y="OS",
    color="PMB Status",
    color_discrete_map=colour_map,
    hover_name="Regimen",
    hover_data=["Condition", "Study"],
    title="Treatment Cost vs Overall Survival"
)

fig.update_xaxes(range=[0, max_cost])

st.plotly_chart(fig, use_container_width=True)

missing_costs = filtered["Cost"].isna().sum()

if missing_costs > 0:
    st.caption(
        f"ℹ️ {missing_costs} treatment(s) are not displayed because treatment costs "
        "were not reported in the source publication."
    )






# -----------------------------
# Table
# -----------------------------
st.subheader("Policy Scenario Analysis")

st.markdown("""
The current **Prescribed Minimum Benefit (PMB)** legislation for advanced
solid-organ malignancies requires a treatment to demonstrate a
**well-demonstrated five-year survival rate greater than 10%**
to satisfy this funding criterion.

The interactive scenario below allows you to explore how treatment
eligibility would change under **alternative policy thresholds**.
This is intended as a policy exploration tool and **does not reflect current legislation**.
""")

policy_threshold = st.slider(
    "Five-year Survival Threshold (%)",
    min_value=1,
    max_value=20,
    value=10
)

sort_option = st.radio(
    "Sort treatments by",
    [
        "Scenario Changes",
        "Highest Cost",
        "Lowest Cost",
        "Highest Survival",
        "Lowest Survival"
    ],
    horizontal=True
)

# Current legislation
filtered["Current Eligible"] = filtered["OS"] > 10

# Scenario legislation
filtered["Scenario Eligible"] = filtered["OS"] > policy_threshold


def scenario_status(row):

    if row["Current Eligible"] and row["Scenario Eligible"]:
        return "Current"

    elif (not row["Current Eligible"]) and row["Scenario Eligible"]:
        return "New"

    elif row["Current Eligible"] and (not row["Scenario Eligible"]):
        return "No Longer Eligible"

    else:
        return "Not Eligible"


filtered["Scenario Status"] = filtered.apply(scenario_status, axis=1)

new_count = (filtered["Scenario Status"] == "New").sum()
lost_count = (filtered["Scenario Status"] == "No Longer Eligible").sum()

st.markdown("###Impact Summary")

if policy_threshold < 10:

    st.info(
        f"""
Lowering the PMB survival threshold to **{policy_threshold}%**
would result in **{new_count} additional treatment(s)** becoming eligible
for funding.

These treatments currently fall just below the legislative threshold of
**10%** and may warrant further clinical investigation or future evidence updates.
"""
    )

elif policy_threshold == 10:

    st.info(
        """
You are viewing the **current South African PMB legislation**.

A treatment must demonstrate a **well-demonstrated five-year survival
greater than 10%** to satisfy this funding criterion.
"""
    )

else:

    st.info(
        f"""
Increasing the PMB survival threshold to **{policy_threshold}%**
would result in **{lost_count} treatment(s)** no longer meeting the
funding criterion.

These treatments currently qualify under legislation but would lose
mandatory funding eligibility under this hypothetical scenario.
"""
    )

scenario_table = (
    filtered[
        ["Regimen", "Condition", "OS", "Cost", "Scenario Status"]
    ]
)

if sort_option == "Scenario Changes":

    scenario_order = {
        "New": 0,
        "No Longer Eligible": 1,
        "Current": 2,
        "Not Eligible": 3
    }

    scenario_table["Order"] = scenario_table["Scenario Status"].map(scenario_order)

    scenario_table = (
        scenario_table
        .sort_values(["Order", "OS"], ascending=[True, False])
        .drop(columns="Order")
    )

elif sort_option == "Highest Cost":

    scenario_table = scenario_table.sort_values(
        "Cost",
        ascending=False,
        na_position="last"
    )

elif sort_option == "Lowest Cost":

    scenario_table = scenario_table.sort_values(
        "Cost",
        ascending=True,
        na_position="last"
    )

elif sort_option == "Highest Survival":

    scenario_table = scenario_table.sort_values(
        "OS",
        ascending=False
    )

elif sort_option == "Lowest Survival":

    scenario_table = scenario_table.sort_values(
        "OS",
        ascending=True
    )

def highlight(row):

    if row["Scenario Status"] == "Current":
        return ["background-color: #d4edda"] * len(row)

    elif row["Scenario Status"] == "New":
        return ["background-color: #cfe2ff"] * len(row)

    elif row["Scenario Status"] == "No Longer Eligible":
        return ["background-color: #f8d7da"] * len(row)

    else:
        return [""] * len(row)



scenario_table["Cost"] = scenario_table["Cost"].apply(
    lambda x: f"R{x:,.2f}" if pd.notna(x) else "-"
)

scenario_table["OS"] = scenario_table["OS"].apply(
    lambda x: f"{x:.1f}%" if pd.notna(x) else "-"
)

st.dataframe(
    scenario_table.style.apply(highlight, axis=1),
    use_container_width=True
)

def highlight_status(row):

    if row["Scenario Status"] == "Current":
        return ["background-color: #d4edda"] * len(row)

    elif row["Scenario Status"] == "New":
        return ["background-color: #cfe2ff"] * len(row)

    elif row["Scenario Status"] == "No Longer Eligible":
        return ["background-color: #f8d7da"] * len(row)

    else:
        return [""] * len(row)



st.markdown("""
🟩 **Green** = Qualified under current legislation (10%)

🟦 **Blue** = Newly qualified under the selected threshold

🟥 **Red** = Lost qualification under the selected threshold
""")
