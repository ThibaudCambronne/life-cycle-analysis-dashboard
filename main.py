import streamlit as st
import pandas as pd
import json
from pathlib import Path
import altair as alt

import lca_calculations

# set the page config (here the title, the tab icon and the layout)
st.set_page_config(page_title="lca-microwave", page_icon=":seedling:", layout="wide", initial_sidebar_state="expanded", menu_items=None)

data_folder = Path("data/")
data_file_path = data_folder / "Holis - Technical test.xlsx"

# ======================== Read the data ========================
# read the data from the customer (info on material, locations and quantities)
with open(data_folder / "dict_data_customers.json", "r") as f:
    dict_data_customers = json.load(f)


# read the data from the database (info on transportation, distances, etc.)
@st.cache_data # cache the data, so that it is not reloaded each time the user changes a parameter
def read_database_sheet():
    df = pd.read_excel(data_file_path, sheet_name="Database", header = 3, index_col=0)

    # remove white spaces at the end and the beginning of the index
    df.index = df.index.str.strip()

    # rename the index of the database to match the name of the material in the customer data
    dict_link_database_to_customer_data = {
        "Plaque de polystyrène, (PS), RER": "Plaque de PPMA",
        "Acier inoxydable, rouleaux, laminés à froid": "Acier",
        "Mix cuivre (99,999% issu de l'électrolyse)": "Fil de cuivre",
        "Transport maritime par porte-conteneurs  [tkm], GLO": "boat",
        "Transport ferroviaire , GLO défaut": "train",
        "Transport en camion [tkm], GLO": "truck",
        "Transport aérien moyen-courrier  [tkm], GLO": "plane"
    }
    df.rename(index=dict_link_database_to_customer_data, inplace=True)

    return df

df_database = read_database_sheet()

# ======================== Get the parameters from dashboard ========================
st.sidebar.header("Product Parameters")
# Life time
dict_data_customers["Usage"]["Duree de vie (annees)"] = st.sidebar.number_input(
    ":green_heart: Life time (years)",
    value=dict_data_customers["Usage"]["Duree de vie (annees)"],
    min_value=1, max_value=30
    )
# Power
dict_data_customers["Usage"]["Puisance (W)"] = st.sidebar.number_input(
    ":zap: Power (W)", value=dict_data_customers["Usage"]["Puisance (W)"], min_value=400, max_value=1000, step=50
    )

# Country of use
list_countries_usage = ["France", "Chine"]

dict_data_customers["Usage"]["Lieu d'utilisation"] = st.sidebar.selectbox(
    ":earth_asia: Country of use",
    list_countries_usage,
    index=list_countries_usage.index(dict_data_customers["Usage"]["Lieu d'utilisation"])
    )

# Country of assembly
dict_data_customers["Processing"]["Lieu d'assemblage"] = st.sidebar.selectbox(
    ":factory: Country of assembly",
    list_countries_usage,
    index=list_countries_usage.index(dict_data_customers["Processing"]["Lieu d'assemblage"])
    )

# Main transport mean
link_transportation_display_to_database = {
    ":truck: Truck": "truck",
    ":train: Train": "train",
    ":boat: Boat": "boat",
    ":airplane: Plane": "plane"
}

main_transportation_mean = st.sidebar.radio(
    ":globe_with_meridians: Main transportation mean",
    list(link_transportation_display_to_database.keys()),
    index=list(link_transportation_display_to_database.values()).index(
        dict_data_customers["Moyen de transport"]["France - Chine"]
    ),
    help="This is the transportation mean between countries (e.g. France - China). The transportation mean within a country is trucks."
)
for i in dict_data_customers["Moyen de transport"].keys():
    dict_data_customers["Moyen de transport"][i] = link_transportation_display_to_database[main_transportation_mean]

st.sidebar.header("Materials Parameters")
# production of the material
list_countries_materials = list_countries_usage + ["Taiwan"]
for i in range(len(dict_data_customers["Materiaux"])):
    material_name = dict_data_customers["Materiaux"][i]["Nom"]
    dict_data_customers["Materiaux"][i]["Lieu de production"] = st.sidebar.selectbox(
        f"Production location of {material_name}",
        list_countries_materials,
        index=list_countries_materials.index(dict_data_customers["Materiaux"][i]["Lieu de production"]),
    )

st.sidebar.caption("Made in collaboration with :link:[Holis](https://holis.earth/) 🌟")


# ======================== Compute the impacts ========================
# compute all the impacts
impact_material = lca_calculations.compute_material_impact(dict_data_customers, df_database)
impact_processing = lca_calculations.compute_impact_processing(dict_data_customers, df_database)
impact_use_phase = lca_calculations.compute_impact_use_phase(dict_data_customers, df_database)
impact_transportation = lca_calculations.compute_impact_transportation(dict_data_customers, df_database)
# sum the impact of the different materials (so that it has the same structure as the other impacts)
impact_material_summed = {i: sum([impact_material[j][i] for j in impact_material.keys()]) for i in impact_material["Plaque de PPMA"].keys()}

# create a dataframe with all the impacts
df_impact = pd.DataFrame.from_dict(impact_material_summed, orient="index", columns=["Material"])
df_impact["Processing"] = impact_processing
df_impact["Use phase"] = impact_use_phase
df_impact["Transportation"] = impact_transportation
df_impact = df_impact.T

# add sum per category in the last row
df_impact.loc["Total per category"] = df_impact.sum()

# convert the different impacts to micropoints, to be able to compare them
conversion_to_micropoints = {
    "kg eq. CO2": 28.6,
    "eq. kBq U235": 12.73,
    "kg eq. Sb": 1395510
}
# Add a row to convert the total of each category of impact to micropoints
df_impact.loc["Total per category (micropoints)"] = [
    df_impact.loc["Total per category", i] * conversion_to_micropoints[i] for i in conversion_to_micropoints.keys()
    ]

# Add a column with the sum of the impacts, per phase, in micropoints
df_impact["Total per phase (micropoints)"] = df_impact["kg eq. CO2"] * conversion_to_micropoints["kg eq. CO2"]
df_impact["Total per phase (micropoints)"] += df_impact["eq. kBq U235"] * conversion_to_micropoints["eq. kBq U235"]
df_impact["Total per phase (micropoints)"] += df_impact["kg eq. Sb"] * conversion_to_micropoints["kg eq. Sb"]

# Add a row with the percentage impact of each category
df_impact.loc["Distribution per indicator (%)"] = df_impact.loc["Total per category (micropoints)", :] / df_impact.loc["Total per category", "Total per phase (micropoints)"] * 100

# add a column with the percentage of the impact of each phase
df_impact["Distribution per phase (%)"] = df_impact["Total per phase (micropoints)"] / df_impact.loc["Total per category", "Total per phase (micropoints)"] * 100

# ======================== Display the results ========================
# Display a first section with information about the app
st.header("Life-Cycle Analysis of a Microwave")
# Functional unit description
st.markdown(f"**Fonctional unit**: cooking food in 3 minutes at a power of {dict_data_customers['Usage']['Puisance (W)']} \
            W, 1200 times a year during {dict_data_customers['Usage']['Duree de vie (annees)']} years.")
# Help about the app
st.markdown("This app is a demo of an interactive dashboard to compute the life cycle analysis of a microwave. \
             You can play with the different parameters to see how they impact the overall impact of the microwave. \
             For instance:  \
            \n- Try changing the :blue[country of use from France to China]. You will see that the \
                    :green[overall impact decreases by 13%], but that the :red[CO2 emissions are multiplied by 5]! \
            \n- Try changing the :blue[main transportation mean from boat to truck]. You will see that it \
                    has barely any impact!")


st.header("Results")
total_micropoints = df_impact.loc["Total per category", "Total per phase (micropoints)"].astype(int)
lifetime = dict_data_customers["Usage"]["Duree de vie (annees)"]
st.markdown(f"The total impact of this product is :orange[{total_micropoints} µPt].")
st.markdown(f":factory: This corresponds to :orange[{(total_micropoints / 1000000 * 100).round(1)} %] of the impact of an average European citizen per year." )

# create columns to display the pie charts
col1, col2, col3 = st.columns([9,1,10])

# display a pie chart for the percentage of the impact of each category (using altair)
chart_width = 500
chart_height = 400
with col1:
    st.subheader("Impact per category", help="More info on the different impacts can be found :link:[here](https://ecochain.com/blog/impact-categories-lca/). \
                 The impacts are expressed in micropoints (µPt) to be able to compare them.")
    st.markdown("Impact of the product divided into 3 categories: \
                \n - :cloud: **Climate change impact** (indicator of potential global warming due \
                    to emissions of greenhouse gases to the air), expressed in kg CO~2 equivalent. \
                \n - :radioactive_sign: **Ionising radiations impact** (damage to human health and ecosystems), \
                    expressed in kBq U235 equivalent. \
                \n - :rock: **Depletion of abiotic resources** (indicator of the depletion of natural ressources), \
                expressed in kg Sb equivalent.")

    distribution_per_indicator = df_impact.loc[["Total per category", "Distribution per indicator (%)"]][
        [i for i in conversion_to_micropoints.keys() if i not in["Total per phase (micropoints)", "Distribution per phase (%)"]]
    ].round(1).T
    
    base = alt.Chart(distribution_per_indicator.reset_index()).encode(
        alt.Theta("Distribution per indicator (%):Q").stack(True),
        alt.Color("index:N").legend(None),
        alt.Tooltip(["index:N", "Distribution per indicator (%):Q", "Total per category:Q"])
        )

    pie = base.mark_arc(outerRadius=100).properties(width=chart_width, height=chart_height)
    text = base.mark_text(radius=160, size=20).encode(text="index:N")

    st.altair_chart(pie + text, use_container_width=True)
    st.caption("Hover over the chart to see the details. The line 'Total per category' \
               corresponds to the total impact of the product in each category and is \
               expressed in the unit under 'index'.")

# display a pie chart for the percentage of the impact of each phase (using altair)
with col3:
    st.subheader("Impact per phase")
    st.markdown("Impact of the products during 4 phases: \
                \n - :hammer_and_wrench: **Material** impact, impact of the production of the different materials. \
                \n - :factory: **Processing** impact, impact of the assembly of the different materials \
                    to make the final product. \
                \n - :house: **Use phase** impact, impact of the use of the product (electicity consumption here). \
                \n - :truck: **Transportation** impact, impact of the transportation of the materials to the \
                    assembly site and of the final product to the customer.")

    distribution_per_phase = df_impact.iloc[:4]["Distribution per phase (%)"].round(1)
    base = alt.Chart(distribution_per_phase.reset_index()).encode(
        alt.Theta("Distribution per phase (%):Q").stack(True),
        alt.Color("index:N").legend(None)
        )

    pie = base.mark_arc(outerRadius=100).properties(width=chart_width, height=chart_height)
    text = base.mark_text(radius=160, size=20).encode(text="index:N")

    st.altair_chart(pie + text, use_container_width=True)

    st.caption("Note: End of life is a very important phase, that is however not included in this demo analysis.")



