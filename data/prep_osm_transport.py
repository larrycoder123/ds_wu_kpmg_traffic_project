# https://download.geofabrik.de/europe/austria.html -> https://download.geofabrik.de/europe/austria-latest.osm.bz2
# https://osm-boundaries.com/map -> osm-boundaries-vienna.poly
# https://wiki.openstreetmap.org/wiki/Osmosis
# https://wiki.openstreetmap.org/wiki/Osmfilter

# osmosis --read-xml austria-latest.osm --bounding-polygon file=osm-boundaries-vienna.poly --write-xml vienna.osm
# osmfilter vienna.osm --keep="public_transport=stop_position" --drop-author --drop-version -o="vienna-public_transport-stop_position.osm"

import os
import json
import pandas as pd
import geopandas as gpd
import xml.etree.ElementTree as ET
from shapely.geometry import Point, shape

file_path_osm = os.path.abspath("data/raw/vienna-public_transport-stop_position.osm")
file_path_osm_output = os.path.abspath("data/public_transport_location.csv")
file_path_geojson = os.path.abspath("data/raw/bezirksgrenzeogd.json")

with open(file_path_geojson, encoding="utf-8") as f:
    geojson_data = json.load(f)

# Convert GeoJSON data into a GeoDataFrame
geo_df = gpd.GeoDataFrame.from_features(geojson_data["features"])

# Set the CRS of the GeoJSON (EPSG:31256) and transform it to WGS 84 (EPSG:4326)
geo_df = geo_df.set_crs("EPSG:31256").to_crs("EPSG:4326")

def has_attribute_value(elements, tag, key, value):
    return any(e.tag == tag and e.get("k") == key and e.get("v") == value for e in elements)

def get_public_transfer_stop_mapping(elements):
    has_railway_station = has_attribute_value(elements, "tag", "railway", "station")
    has_railway_halt = has_attribute_value(elements, "tag", "railway", "halt")
    has_railway_stop = has_attribute_value(elements, "tag", "railway", "stop")
    has_subway_station = has_attribute_value(elements, "tag", "station", "subway")
    has_subway_yes = has_attribute_value(elements, "tag", "subway", "yes")    
    has_bus_yes = has_attribute_value(elements, "tag", "bus", "yes")
    has_station_miniature = has_attribute_value(elements, "tag", "station", "miniature")
    has_operator_wlb = has_attribute_value(elements, "tag", "operator", "WLB")
    has_light_rail = has_attribute_value(elements, "tag", "light_rail", "yes")
    has_tram_yes = has_attribute_value(elements, "tag", "tram", "yes")
    has_train_yes = has_attribute_value(elements, "tag", "train", "yes")
    has_highway_bus_stop = has_attribute_value(elements, "tag", "highway", "bus_stop")

    if (has_railway_station and has_subway_station) or (has_subway_yes):
        return "U-Bahn"
    
    if has_railway_station and not has_subway_station and not has_station_miniature and not has_operator_wlb:
        return "Zug"
    
    if has_railway_halt and not has_subway_station and not has_station_miniature and not has_operator_wlb:
        return "Zug"
    
    if has_railway_stop or has_train_yes:
        return "Zug"
    
    if has_bus_yes or has_highway_bus_stop:
        return "Bus"
    
    if has_light_rail or has_tram_yes:
        return "Straßenbahn"        
    
    return None # return "Unbekannt" # enable for debug

# Function to find the corresponding district
def find_district(lon, lat):
    point = Point(lon, lat)
    for _, row in geo_df.iterrows():
        if shape(row["geometry"]).contains(point):
            return row.get("STATAUSTRIA_BEZ_CODE", "Unknown")
        
    return "Unknown"

tree = ET.parse(file_path_osm)
root = tree.getroot()

# Extract public transport stops
stops_data = []

id = 1

for node in root.findall("node"):
    stop_name = None
    lat = node.get("lat")
    lon = node.get("lon")        
    elements = node.findall("tag")        
    
    if has_attribute_value(elements, "tag", "operator", "Liliputbahn im Prater GmbH") or \
        has_attribute_value(elements, "tag", "name", "Einkehr zur Zahnradbahn, Zahnradbahnstraße") or \
        has_attribute_value(elements, "tag", "railway", "construction") or \
        has_attribute_value(elements, "tag", "ferry", "yes"):
        continue

    for tag in elements:
        if tag.get("k") == "name":
            stop_name = tag.get("v")
            break

    category = get_public_transfer_stop_mapping(elements)

    district_code = find_district(lon, lat)

    if stop_name and category:
        stops_data.append({"Id": id, "Name": stop_name, "Latitude": lat, "Longitude": lon, "Kategorie": category, "Bezirk_Code": district_code})
        id = id + 1

df = pd.DataFrame(stops_data)
df.to_csv(file_path_osm_output, index=False, encoding="UTF-8")
