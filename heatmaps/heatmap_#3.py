import os
import pandas as pd
import folium
from folium.plugins import HeatMap

# === Forecast-Daten laden ===
kfz_df = pd.read_csv("./prophet_forecasts/data/district_forecast_Kfz.csv")
lkw_df = pd.read_csv("./prophet_forecasts/data/district_forecast_Lkw.csv")
locations_df = pd.read_csv("./data/dauerzaehlstellen_location.csv")

# === Datumsformat und Filter ===
kfz_df['ds'] = pd.to_datetime(kfz_df['ds'])
lkw_df['ds'] = pd.to_datetime(lkw_df['ds'])

kfz_dec = kfz_df[kfz_df['ds'] == '2025-12-31']
lkw_dec = lkw_df[lkw_df['ds'] == '2025-12-31']

# === Zusammenführen mit Location-Daten ===
kfz_merged = pd.merge(kfz_dec, locations_df, left_on="znr", right_on="ZNR")
lkw_merged = pd.merge(lkw_dec, locations_df, left_on="znr", right_on="ZNR")

# === Heatmap-Daten vorbereiten ===
kfz_heat_data = [
    [row["LATITUDE"], row["LONGITUDE"], row["yhat"]] for _, row in kfz_merged.iterrows()
]
lkw_heat_data = [
    [row["LATITUDE"], row["LONGITUDE"], row["yhat"]] for _, row in lkw_merged.iterrows()
]

# === Karte erstellen ===
vienna_center = [48.2082, 16.3738]
m = folium.Map(location=vienna_center, zoom_start=12, tiles="cartodbpositron")

# === HeatMaps hinzufügen ===
HeatMap(kfz_heat_data, radius=25, blur=20, max_zoom=13, name="Kfz-Prognose").add_to(m)
HeatMap(lkw_heat_data, radius=25, blur=20, max_zoom=13, name="Lkw-Prognose", gradient={0.2: 'blue', 0.5: 'orange', 1.0: 'red'}).add_to(m)

# === Layer Control aktivieren ===
folium.LayerControl().add_to(m)

# === Legende einfügen ===
legend_html = """
<div style="
    position: fixed;
    bottom: 50px;
    left: 50px;
    width: 240px;
    background-color: white;
    border:2px solid grey;
    z-index:9999;
    font-size:14px;
    padding: 10px;">
    <b>Predicted Traffic Density</b><br>
    <i>December 2025</i><br><br>

    <b style="color:black">Passenger Cars (default color scale)</b><br>
    <div style="background:linear-gradient(to right, blue, lime, red); height: 10px;"></div>
    <span style="float:left">low</span>
    <span style="float:right">high</span>
    <div style="clear:both;"></div><br>

    <b style="color:black">Trucks (Blue-Orange-Red)</b><br>
    <div style="background:linear-gradient(to right, blue, orange, red); height: 10px;"></div>
    <span style="float:left">low</span>
    <span style="float:right">high</span>
    <div style="clear:both;"></div>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# === Karte speichern ===
m.save("forecast_heatmap_kfz_lkw_2025.html")
print("Heatmap gespeichert als: forecast_heatmap_kfz_lkw_2025.html")
