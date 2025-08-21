import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape

file_path_location = os.path.abspath("data/raw/dauerzaehlogd.csv")
file_path_location_cleaned = os.path.abspath("data/dauerzaehlstellen_location.csv")
file_path_geojson = os.path.abspath("data/raw/bezirksgrenzeogd.json")

df = pd.read_csv(file_path_location)

with open(file_path_geojson, encoding="utf-8") as f:
    geojson_data = json.load(f)

# Convert GeoJSON data into a GeoDataFrame
geo_df = gpd.GeoDataFrame.from_features(geojson_data["features"])

# Set the CRS of the GeoJSON (EPSG:31256) and transform it to WGS 84 (EPSG:4326)
geo_df = geo_df.set_crs("EPSG:31256").to_crs("EPSG:4326")

# Extract coordinates from SHAPE Column
df[["LONGITUDE", "LATITUDE"]] = df["SHAPE"].str.extract(r"POINT \(([-\d\.]+) ([-\d\.]+)\)")
df["LONGITUDE"] = df["LONGITUDE"].astype(float)
df["LATITUDE"] = df["LATITUDE"].astype(float)

# Function to find the corresponding district
def find_district(lon, lat):
    point = Point(lon, lat)
    for _, row in geo_df.iterrows():
        if shape(row["geometry"]).contains(point):
            return row.get("NAMEK", "Unknown"), row.get("DISTRICT_CODE", "Unknown"), row.get("BEZNR", "Unknown"), row.get("STATAUSTRIA_BEZ_CODE", "Unknown")
    return "Unknown", "Unknown", "Unknown", "Unknown"

# Assign district data to each row
df[["BEZIRK_NAME", "BEZIRK_PLZ", "BEZIRK_NR", "BEZIRK_CODE"]] = df.apply(lambda row: pd.Series(find_district(row["LONGITUDE"], row["LATITUDE"])), axis=1)

df.drop(columns=["FID", "OBJECTID", "SHAPE", "BETRIEBNAHME", "LAGE", "GERAETEART", "GERAETEART_TXT", "SE_ANNO_CAD_DATA"], inplace=True)

df.rename(columns={"ZST_ID": "ZNR"}, inplace=True)
df.rename(columns={"ZST_NAME": "ZNAME"}, inplace=True)
df.rename(columns={"STR_NR": "STRNR"}, inplace=True)
df = df.sort_values(by="ZNR")

df.to_csv(file_path_location_cleaned, index=False, encoding="utf-8")
