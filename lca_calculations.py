def compute_material_impact(dict_data_customers, df_database):
    dict_impact_material = {}

    for i in range(len(dict_data_customers["Materiaux"])):
        material_name = dict_data_customers["Materiaux"][i]["Nom"]
        dict_impact_material[material_name] = {}

        for col in df_database.columns:
            if col != "Unit":
                try:
                    dict_impact_material[material_name][col] = (
                        df_database.loc[material_name, col] * dict_data_customers["Materiaux"][i]["Masse utile (kg)"]
                    )
                    
                except KeyError:
                    print(f"Warning: {col} emissions fo material {material_name} not found in the database (defaulted to 0)")
                    dict_impact_material[material_name][col] = 0

    return dict_impact_material


def compute_impact_processing(dict_data_customers, df_database):
    dict_link_electricity_country_to_database = {
        "France": "Mix électrique réseau, FR",
        "Chine": "Mix électrique réseau, CN"
    }

    dict_impact_processing = {}
    processing_electricity = dict_data_customers["Processing"]["Consommation d'energie (kWh)"]
    processing_country = dict_data_customers["Processing"]["Lieu d'assemblage"]

    for col in df_database.columns:
        if col != "Unit":
            dict_impact_processing[col] = (
                df_database.loc[
                    dict_link_electricity_country_to_database[processing_country], col] * 
                    processing_electricity
            )
                

    return dict_impact_processing


def compute_impact_use_phase(dict_data_customers, df_database):
    dict_link_electricity_country_to_database = {
        "France": "Mix électrique réseau, FR",
        "Chine": "Mix électrique réseau, CN"
    }

    dict_impact_use_phase = {}
    use_phase_electricity_kw = (
        dict_data_customers["Usage"]["Duree de vie (annees)"] * 
        dict_data_customers["Usage"]["Nombre de cycles par an"] * 
        dict_data_customers["Usage"]["Puisance (W)"] * 
        dict_data_customers["Usage"]["Duree de cycle (min)"] 
        / 60 # convert minutes to hours
        / 1000 # convert W to kW
    )
    use_phase_country = dict_data_customers["Usage"]["Lieu d'utilisation"]

    for col in df_database.columns:
        if col != "Unit":
            dict_impact_use_phase[col] = (
                df_database.loc[
                    dict_link_electricity_country_to_database[use_phase_country], col
                    ] * use_phase_electricity_kw
            )
                

    return dict_impact_use_phase


# data for the trips distance, source: https://www.searates.com/fr/services/distances-time/
# the distance can be divided by 2 for plane trips
distance_trips = {
    "France - France": 600,
    "France - Chine": 18775,
    "France - Taiwan": 18075,
    "Chine - Taiwan": 850,
    "Chine - Chine": 1900,
    "Taiwan - Taiwan": 600
}


def get_trip_index(dict_with_info, str_a, str_b):
    """Get the info in a dict where the key looks like either 'France - Chine' or 'Chine - France'

    Args:
        dict_with_info (dict): dict with the info
        str_a (str): first country
        str_b (str): second country

    Returns:
        info: the info found in the dict
    """
    try:
        info = dict_with_info[f"{str_a} - {str_b}"]
    except KeyError:
        try:
            info = dict_with_info[f"{str_b} - {str_a}"]
        except KeyError:
            raise KeyError(f"Warning: distance for trip {str_a} - {str_b} not found in the database")
    
    return info


def get_distance_trip(country_from, counrty_to, transportation_mean):
    distance = get_trip_index(distance_trips, country_from, counrty_to)
    
    if transportation_mean == "plane":
        distance /= 2
    return distance


def compute_distance_single_transport(country_from, counrty_to, transportation_mean):
    dict_distance_transport = {i: 0 for i in ["train", "truck", "plane", "boat"]}

    # create the list of trips to do
    if country_from == counrty_to:
        list_trips = [(country_from, country_from, "truck")]
    else:
        list_trips = [
            (country_from, country_from, "truck"),
            (country_from, counrty_to, transportation_mean),
            (counrty_to, counrty_to, "truck")
        ]
    
    for trip in list_trips:
        trip_from = trip[0]
        trip_to = trip[1]
        trip_transportation_mean = trip[2]
        dict_distance_transport[trip_transportation_mean] += get_distance_trip(trip_from, trip_to, trip_transportation_mean)

    return dict_distance_transport


def compute_tkm_transportation(dict_data_customers):
    dict_tkm_transport = {i: 0 for i in ["train", "truck", "plane", "boat"]}

    for i in range(len(dict_data_customers["Materiaux"])):
        raw_mass = dict_data_customers["Materiaux"][i]["Masse utile (kg)"] # in kg, before processing losses
        country_from = dict_data_customers["Materiaux"][i]["Lieu de production"]
        country_to = dict_data_customers["Processing"]["Lieu d'assemblage"]
        
        # get the transportation mean
        try:
            transportation_mean = get_trip_index(dict_data_customers["Moyen de transport"], country_from, country_to)
            print("here", transportation_mean)
        except KeyError:
            transportation_mean = "truck"

        dict_distance_transport_material = compute_distance_single_transport(
            country_from,
            country_to,
            transportation_mean
        )

        # Convert the distances to tkm
        for transportation_mean in dict_distance_transport_material.keys():
            dict_tkm_transport[transportation_mean] += (
                dict_distance_transport_material[transportation_mean] *
                raw_mass / 1000 # convert kg to t
            )
    
    # add the transportation for the processing
    country_from = dict_data_customers["Processing"]["Lieu d'assemblage"]
    country_to = dict_data_customers["Usage"]["Lieu d'utilisation"]
    # get the transportation mean between the two countries
    try:
        transportation_mean = get_trip_index(dict_data_customers["Moyen de transport"], country_from, country_to)
    except KeyError:
        transportation_mean = "truck"

    dict_distance_transport_processing = compute_distance_single_transport(
        country_from,
        country_to,
        "truck"
    )
    mass_end_product = sum([i["Masse produit fini (kg)"] for i in dict_data_customers["Materiaux"]])

    # Convert the distances to tkm
    for transportation_mean in dict_distance_transport_processing.keys():
        dict_tkm_transport[transportation_mean] += (
            dict_distance_transport_processing[transportation_mean] *
            mass_end_product / 1000 # convert kg to t
        )

    return dict_tkm_transport


def compute_impact_transportation(dict_data_customers, df_database):
    dict_impact_transportation = {i: 0 for i in df_database.columns if i != "Unit"}

    dict_tkm_transport = compute_tkm_transportation(dict_data_customers)

    for col in dict_impact_transportation.keys():
            for transportation_mean in dict_tkm_transport.keys():
                dict_impact_transportation[col] += (
                    df_database.loc[transportation_mean, col] * dict_tkm_transport[transportation_mean]
                )
    
    return dict_impact_transportation