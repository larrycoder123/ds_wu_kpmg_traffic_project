import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Paths
data_location = os.path.abspath("./data/processed_data/dauerzaehlstellen_location.csv")
data_traffic = os.path.abspath("./data/processed_data/dauerzaehlstellen_data.csv") 
output_path = os.path.abspath("output/traffic_heatmap.png")

# Load data
location_df = pd.read_csv(data_location)
traffic_df = pd.read_csv(data_traffic)

# Merge location and traffic data on ZNR (station ID)
merged_df = pd.merge(location_df, traffic_df, on="ZNR")

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(
    merged_df,
    geometry=gpd.points_from_xy(merged_df.LONGITUDE, merged_df.LATITUDE),
    crs="EPSG:4326"
)

# Load Bezirksgrenzen
boundary_path = os.path.abspath("./data/raw_data/bezirksgrenzeogd.json")
boundary_gdf = gpd.read_file(boundary_path)

# Transform CRS if necessary
boundary_gdf = boundary_gdf.to_crs("EPSG:4326")

# Plotting
fig, ax = plt.subplots(figsize=(12, 12))

# Plot District Boundaries
boundary_gdf.boundary.plot(ax=ax, linewidth=1, color="black")

# Plot Traffic Points
gdf.plot(
    ax=ax,
    markersize=gdf["TVMAX"] / 100,
    alpha=0.6,
    color="blue"
)

plt.title("Heatmap of Traffic Density in Vienna with Districts")
plt.axis("off")

# Custom Legend
for size in [25000, 50000, 75000, 100000]:
    plt.scatter([], [], s=size/100, c="blue", alpha=0.6,
                label=f"Maximaler Tagesverkehr in Fahrzeugen ~ {size:,}".replace(",", "."))

plt.legend(scatterpoints=1, frameon=True, labelspacing=1, title="Traffic Volume", loc="lower left")

plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.show()