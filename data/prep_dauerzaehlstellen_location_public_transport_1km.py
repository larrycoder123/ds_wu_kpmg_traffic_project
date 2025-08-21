import os
import pandas as pd
from geopy.distance import geodesic

file_path_location = os.path.abspath("data/dauerzaehlstellen_location.csv")
file_path_transport = os.path.abspath("data/public_transport_location.csv")
file_path_output = os.path.abspath("data/dauerzaehlstellen_location_public_transport_1km.csv")

dauerzaehlstellen_df = pd.read_csv(file_path_location)
public_transport_df = pd.read_csv(file_path_transport)

results = []

for _, dz_row in dauerzaehlstellen_df.iterrows():
    dz_coords = (dz_row["LATITUDE"], dz_row["LONGITUDE"])
    dz_znr = dz_row["ZNR"]

    for _, pt_row in public_transport_df.iterrows():
        pt_coords = (pt_row["Latitude"], pt_row["Longitude"])
        pt_id = pt_row["Id"]
        
        distance_km = geodesic(dz_coords, pt_coords).kilometers
        
        if distance_km <= 1 :
            results.append({"ZNR": dz_znr, "Public_Transport_Id": pt_id})

result_df = pd.DataFrame(results)

result_df.to_csv(file_path_output, index=False)
