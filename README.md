# Vienna Traffic Forecasting & Analysis

A comprehensive data science project analyzing and forecasting traffic patterns at Vienna's permanent counting stations. Combines historical traffic data, geospatial analysis, and time series modeling to deliver station-level predictions through an interactive Dash dashboard.

## Overview

This project processes multi-year traffic data from Vienna's permanent counting stations (Dauerzählstellen) to forecast future traffic volumes and analyze spatial patterns. The analysis integrates public transport infrastructure, district boundaries, and population data to provide contextual insights into traffic dynamics across the city.

**Collaboration**: WU Vienna & KPMG final project by 4 data science students

**Dataset**: Historical traffic counts from Vienna's permanent counting stations, including vehicle types (Kfz - all vehicles, Lkw - trucks), daily patterns, and location metadata across 23 districts.

## Key Features

- **Time Series Forecasting**: Prophet-based models predicting traffic volumes up to 2032
- **COVID-19 Impact Analysis**: Specialized forecasts accounting for pandemic-induced traffic pattern changes
- **Interactive Dashboard**: Real-time exploration of historical data and forecasts via Dash/Plotly
- **Geospatial Clustering**: K-means clustering of counting stations by traffic patterns
- **Heatmap Visualizations**: Spatial distribution of traffic intensity with district overlays
- **Regression Analysis**: Impact of public transport proximity on traffic volumes

## Tech Stack

**Languages & Core Libraries**
- Python, R, Pandas, NumPy, tidyverse

**Time Series & Forecasting**
- Prophet (Facebook's forecasting library)
- SARIMAX (statsmodels)

**Geospatial Analysis**
- GeoPandas, Shapely
- Folium, Leaflet
- OpenStreetMap data processing

**Machine Learning & Statistics**
- scikit-learn (clustering, metrics)
- R clustering (factoextra, cluster)

**Visualization & Dashboard**
- Dash, Plotly
- Matplotlib, ggplot2
- Dash Leaflet (interactive maps)

**Development**
- Jupyter Notebooks, RMarkdown

## Project Structure

```
code/
├── dashboard/
│   ├── dashboard.py                    # Main interactive Dash application
│   └── forecasts_dashboard/
│       ├── forecasting.ipynb           # SARIMAX & Prophet model training
│       ├── combine_data.ipynb          # Data pipeline integration
│       └── traffic_dashboard_final.csv # Dashboard data feed
├── prophet_forecasts/
│   ├── generate_district_forecast.py   # District-level Prophet forecasts
│   ├── generate_corona_forecast.py     # COVID-19 adjusted predictions
│   └── data/                           # Forecast outputs (2032 projections)
├── analysis/
│   ├── analysis_clustering.Rmd         # K-means clustering of stations
│   ├── analysis_regression_public_transport.Rmd
│   └── City_Centre_vs_Suburbs.ipynb    # Urban pattern comparisons
├── heatmaps/
│   ├── heatmap_#1.py                   # Traffic density visualizations
│   ├── heatmap_#2.py                   # Forecast heatmaps with Folium
│   └── output/                         # Generated heatmap HTML files
└── data/
    ├── prep_dauerzaehlstellen_data.py  # Traffic data preprocessing
    ├── prep_osm_transport.py           # Public transport location extraction
    ├── processed_data/                 # Clean datasets for analysis
    └── raw_data/                       # Original Vienna Open Data files
```

## Key Findings

- **Temporal Patterns**: Clear weekday vs. weekend traffic distinctions with Friday and Monday peaks
- **COVID-19 Impact**: Significant traffic reduction during 2020-2022, requiring adjusted forecasting models
- **Spatial Clustering**: Identified 3 distinct station clusters based on daily traffic patterns (city center high-volume, suburban moderate, low-traffic peripheral)
- **Public Transport Influence**: Negative correlation between public transport stop density and vehicle traffic at counting stations
- **District Variability**: Inner districts show higher truck percentages; outer districts show stronger weekend traffic patterns
- **Forecast Accuracy**: Prophet models successfully captured seasonal patterns and long-term trends for 2025-2032 projections

## Documentation

- **Report**: See `project_report.pdf` for detailed methodology, statistical analysis, and visualizations
- **Presentation**: See `presentation.pdf` for executive summary and key insights
