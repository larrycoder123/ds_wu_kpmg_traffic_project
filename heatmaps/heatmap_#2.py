import os
import pandas as pd
import folium
from folium.plugins import HeatMap

# === 1. Forecast-Daten laden und filtern ===
forecast_df = pd.read_csv("./prophet_forecasts/data/district_forecast_Kfz.csv")  
forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])

# Filter: nur Dezember 2025
forecast_dec2025 = forecast_df[forecast_df['ds'] == '2025-12-31']

# === 2. Zählstellen-Standorte laden ===
locations_df = pd.read_csv("./data/data_processed/dauerzaehlstellen_location.csv")  # Pfad anpassen bei Bedarf

# === 3. Daten zusammenführen ===
merged_df = pd.merge(forecast_dec2025, locations_df, left_on="znr", right_on="ZNR")

# === 4. Heatmap-Daten vorbereiten ===
# Format: [Latitude, Longitude, Gewicht]
heat_data = [
    [row["LATITUDE"], row["LONGITUDE"], row["yhat"]]
    for _, row in merged_df.iterrows()
]

# === 5. Interaktive Karte erzeugen ===
vienna_center = [48.2082, 16.3738]  # Zentrum Wiens
m = folium.Map(location=vienna_center, zoom_start=12, tiles="cartodbpositron")

# Heatmap hinzufügen
HeatMap(heat_data, radius=18, blur=15, max_zoom=13).add_to(m)


# === HTML-Legende ===
legend_html = """
<div style="
    position: fixed;
    bottom: 50px;
    left: 50px;
    width: 180px;
    height: 130px;
    background-color: white;
    border:2px solid grey;
    z-index:9999;
    font-size:14px;
    padding: 10px;
    ">
    <b>Prognostizierte Kfz-Intensität</b><br>
    <i>Dezember 2025</i><br>
    <div style="background:linear-gradient(to right, blue, lime, red); height: 10px;"></div>
    <span style="float:left">niedrig</span>
    <span style="float:right">hoch</span>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# === 6. Karte speichern ===
m.save("forecast_heatmap_kfz_2025.html")
print("Heatmap gespeichert als: forecast_heatmap_kfz_2025.html")


