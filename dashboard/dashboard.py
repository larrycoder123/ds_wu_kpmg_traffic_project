import dash
from dash import html, dcc, Output, Input, State
import dash_leaflet as dl
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os # <-- Import the 'os' module

# --- 1. Load and Preprocess Data ---
# Initialize variables to hold data and slider configuration
df = pd.DataFrame()
# Initialize as a simple list. A PeriodIndex requires a frequency when empty.
unique_year_months = []
slider_marks = {}

try:
    # --- Hardcoded Path ---
    # Using the specific hardcoded path as requested by the user.
    csv_path = "dashboard/forecasts_dashboard/traffic_dashboard_final.csv"
    
    # Attempt to load the dataset using the full path
    print(f"Attempting to load data from: {csv_path}")
    df = pd.read_csv(csv_path)

    # If loading is successful, proceed with all data processing
    if not df.empty:
        df['DATE'] = pd.to_datetime(df['DATE'])
        df['YEAR'] = df['DATE'].dt.year
        df = df.sort_values('DATE')

        # Create the list of unique year-months for the slider
        # The result of .unique() is a PeriodArray, which we convert to a sortable PeriodIndex.
        unique_periods = df['DATE'].dt.to_period('M').unique()
        unique_year_months = pd.PeriodIndex(unique_periods).sort_values()


        # Create labels for the slider's marks, showing only years and hiding intermediate numbers
        slider_marks = {}
        for i, date in enumerate(unique_year_months):
            # Handle the very last entry specifically to set its label correctly
            if i == len(unique_year_months) - 1:
                # If the last month is December, label this tick with the next year to signify the end of the range.
                if date.month == 12:
                    slider_marks[i] = str(date.year + 1)
                else: # Otherwise, just use its own year.
                    slider_marks[i] = date.strftime('%Y')
            # Show the year for the first month of the year, or for the very first entry
            elif date.month == 1 or i == 0:
                slider_marks[i] = date.strftime('%Y')
            else:
                # For all other marks, provide an empty string to hide the default number
                slider_marks[i] = ''

except FileNotFoundError:
    # This error will now be much more specific if it occurs.
    print(f"Error: Could not find 'traffic_dashboard_final.csv' at the expected path: {csv_path}")
    print("Please ensure the CSV file is in the same directory as the script.")
except Exception as e:
    # Catch other potential errors during processing
    print(f"An error occurred during data processing: {e}")


# --- 2. Dash App Initialization ---
app = dash.Dash(__name__, suppress_callback_exceptions=True, title="Vienna Car Traffic Forecast Dashboard")

# --- 3. Main Application Layout ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9', 'padding': '20px', 'position': 'relative'}, children=[
    # Add the logo here
    html.Img(
        src='assets/KPMGWU.png',  # The path to your logo file within the assets folder
        style={
            'position': 'absolute',
            'top': '15px',
            'left': '15px',
            'height': '90px', # Adjust height as needed
        }
    ),
    html.H1("Vienna Car Traffic Forecast Dashboard", style={'textAlign': 'center', 'color': '#333'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# --- 4. Page Layouts (Functions) ---

def layout_index():
    """
    Generates the layout for the main page (map view).
    If the dataframe is empty (due to FileNotFoundError), it will display an error message.
    """
    if df.empty:
        return html.Div([
            html.H3("Error: Data Could Not Be Loaded", style={'color': 'red', 'textAlign': 'center'}),
            html.P("Please check the console output for a 'FileNotFoundError'. Make sure that 'traffic_dashboard_final.csv' is in the same directory as your Python script.", style={'textAlign': 'center'})
        ], style={'padding': '50px', 'margin': 'auto', 'width': '60%', 'border': '2px dashed red', 'borderRadius': '10px'})

    return html.Div([
        html.P("Select a month and year to see the traffic data for Vienna's counting stations.", style={'textAlign': 'center'}),
        # Time slider for selecting the month
        dcc.Slider(
            id='month-slider',
            min=0,
            max=len(unique_year_months) - 1,
            step=1,
            value=unique_year_months.get_loc(pd.to_datetime('2024-12-01').to_period('M')) if pd.to_datetime('2024-12-01').to_period('M') in unique_year_months else 0, # Default to Dec 2024
            marks=slider_marks,
            # Tooltip has been removed to hide the hover-over number
        ),
        html.Div(id='slider-output-container', style={'textAlign': 'center', 'marginTop': '10px', 'fontSize': '1.2em'}),
        # Leaflet map to display the stations
        dl.Map(
            center=[48.2082, 16.3738], zoom=12,
            children=[
                dl.TileLayer(
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                ),
                dl.LayerGroup(id='marker-layer')
            ],
            style={'width': '100%', 'height': '60vh', 'marginTop': '20px', 'borderRadius': '8px'}
        ),
    ])

def layout_detail(station_id):
    """
    Generates the layout for the detail page of a specific counting station.
    """
    try:
        station_id = int(station_id)
        # Filter the main dataframe for the selected station
        station_data = df[df['ZNR'] == station_id].sort_values('DATE')

        if station_data.empty:
            return html.Div([
                html.H3(f"No data found for station ID: {station_id}"),
                dcc.Link("← Back to Map", href="/")
            ])

        station_name = station_data['ZNAME'].iloc[0]
        bezirk_name = station_data['BEZIRK_NAME'].iloc[0]
        bezirk_nr = int(station_data['BEZIRK'].iloc[0])
        znr = station_data['ZNR'].iloc[0]
        lat = station_data['LATITUDE'].iloc[0]
        lon = station_data['LONGITUDE'].iloc[0]
        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        
        # --- Main Time Series Plot ---
        fig_main = go.Figure()

        # 1. Historical Data (DTVMS)
        hist_data = station_data[station_data['DATE'].dt.year <= 2024]
        fig_main.add_trace(go.Scatter(
            x=hist_data['DATE'], y=hist_data['DTVMS'],
            mode='lines', name='Historical Traffic Volume',
            line=dict(color='#007bff', width=2.5)
        ))

        # 2. Forecast Data
        fc_data = station_data[station_data['DATE'].dt.year >= 2025]
        forecast_models = {
            'DTVMS_ensemble': ('Forecast (Ensemble)', '#dc3545', 3),
            'DTVMS_full_exog': ('Forecast (Exog)', '#28a745', 1.5),
            'DTVMS_full_noex': ('Forecast (No Exog)', '#ffc107', 1.5),
            'DTVMS_full_prophet': ('Forecast (Prophet)', '#17a2b8', 1.5)
        }
        for col, (name, color, width) in forecast_models.items():
            fig_main.add_trace(go.Scatter(
                x=fc_data['DATE'], y=fc_data[col],
                mode='lines', name=name,
                line=dict(color=color, width=width, dash='dot' if 'Ensemble' not in name else 'solid'),
                opacity=0.8
            ))

        # 3. COVID-19 Period Highlight
        covid_dates = station_data[station_data['ISTCOVID19'] == 1]['DATE']
        if not covid_dates.empty:
            fig_main.add_vrect(
                x0=covid_dates.min(), x1=covid_dates.max(),
                annotation_text="COVID-19 Period", annotation_position="top left",
                fillcolor="yellow", opacity=0.15, line_width=0 # Made more transparent
            )

        fig_main.update_layout(
            title=dict(text=f"Traffic Volume: Historical and Forecast for {station_name}", x=0.5),
            xaxis_title="Date",
            yaxis_title="Traffic Volume",
            legend_title="Data Series",
            template='plotly_white',
            margin=dict(l=20, r=20, t=40, b=20)
        )

        # Disclaimer for the forecast model and DTVMS explanation
        traffic_volume_explanation = "Traffic Volume represents the average number of vehicles counted over a 24-hour period (Monday-Sunday)."
        disclaimer_text = html.Div([
            html.P([html.Strong("About the data: "), traffic_volume_explanation], style={'marginBottom': '5px'}),
            html.P([
                html.Strong("About the Ensemble Forecast: "),
                "The main forecast ('Ensemble') is a weighted average of three models: Prophet (30%), SARIMA (68%), and SARIMAX (2%)."
            ])
        ], style={'fontSize': '0.9em', 'color': '#6c757d', 'textAlign': 'center', 'marginTop': '10px'})


        # --- Exogenous Variables Plots ---
        fig_exog = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "District Population Over Time", "District Commuter Rate (%)", 
                "District Car Density Over Time", "Yearly Vienna Traffic Share (%)"
            ),
            specs=[[{'type': 'xy'}, {'type': 'xy'}], # Using 'xy' for line charts
                   [{'type': 'xy'}, {'type': 'bar'}]]
        )
        
        # Plot 1: Population Time Series
        fig_exog.add_trace(go.Scatter(
            x=station_data['DATE'], y=station_data['POP'], 
            mode='lines', name='Population', line=dict(color='#636EFA')
        ), row=1, col=1)

        # Plot 2: Commuters Time Series
        fig_exog.add_trace(go.Scatter(
            x=station_data['DATE'], y=station_data['AUSPENDLER'], 
            mode='lines', name='Commuter Rate', line=dict(color='#EF553B')
        ), row=1, col=2)

        # Plot 3: Car Density Time Series
        fig_exog.add_trace(go.Scatter(
            x=station_data['DATE'], y=station_data['PKW_DENSITY'], 
            mode='lines', name='Car Density', line=dict(color='#00CC96')
        ), row=2, col=1)

        # Plot 4: Traffic Share (Yearly Stacked Bar Chart)
        traffic_share_cols = ['CAR', 'PUBLIC_TRANSPORT', 'BY_FOOT', 'BIKE']
        # Calculate yearly average for the traffic share percentages
        yearly_share = station_data.groupby('YEAR')[traffic_share_cols].mean().reset_index()

        for col, color in zip(traffic_share_cols, ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']):
            fig_exog.add_trace(go.Bar(
                x=yearly_share['YEAR'], 
                y=yearly_share[col], 
                name=col.replace('_', ' ').title()
            ), row=2, col=2)

        fig_exog.update_layout(
            barmode='stack', # Stack the bars for the traffic share
            title=dict(text="Exogenous Factors Over Time and City-Wide Traffic Share", x=0.5),
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5), # Legend moved further down
            height=600,
            template='plotly_white', # Set background to white
            margin=dict(l=40, r=20, t=100, b=150) # Increased bottom margin for legend
        )
        # Add axis titles for clarity
        fig_exog.update_xaxes(title_text="Date", row=1, col=1)
        fig_exog.update_xaxes(title_text="Date", row=1, col=2)
        fig_exog.update_xaxes(title_text="Date", row=2, col=1)
        fig_exog.update_xaxes(title_text="Year", row=2, col=2)
        fig_exog.update_yaxes(title_text="Population", row=1, col=1)
        fig_exog.update_yaxes(title_text="Rate (%)", row=1, col=2)
        fig_exog.update_yaxes(title_text="Cars per 1000", row=2, col=1)
        fig_exog.update_yaxes(title_text="Share (%)", row=2, col=2)
        
        exog_disclaimer = html.P(
            "Note: The data for the exogenous variables (Population, Commuters, Car Density) was forecasted from 2025 onwards using an ARIMA model.",
            style={'fontSize': '0.9em', 'color': '#6c757d', 'textAlign': 'center', 'marginTop': '10px'}
        )

        # Add vertical spacing
        station_info_style = {'textAlign': 'center', 'color': '#6c757d', 'marginBottom': '25px'}
        graph_style = {'marginBottom': '25px'}
        hr_style = {'marginBottom': '25px'}
        p_style = {'margin': '4px 0'} # Spacing for each line of station info

        return html.Div([
            dcc.Link("← Back to Map", href="/", style={'textDecoration': 'none', 'color': '#007bff', 'fontSize': '16px'}),
            html.Div(f"Details for Station: {station_name}", style={'textAlign': 'center', 'fontSize': '1.5em', 'fontWeight': 'bold', 'marginTop': '15px'}),
            html.Div([
                html.P(f"District Name: {bezirk_name}", style=p_style),
                html.P(f"District Code: {bezirk_nr}", style=p_style),
                html.P(f"Counter ZNR: {znr}", style=p_style),
                html.A("View on Google Maps", href=gmaps_link, target="_blank", style={'color': '#5CACEE'}) # Lighter blue link
            ], style=station_info_style),
            html.Div(dcc.Graph(figure=fig_main), style=graph_style),
            disclaimer_text,
            html.Hr(style=hr_style),
            html.Div(dcc.Graph(figure=fig_exog), style=graph_style),
            exog_disclaimer
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'})

    except (ValueError, IndexError) as e:
        return html.Div([
            html.H3("Error processing this station.", style={'color': 'red'}),
            html.P(f"Details: {e}"),
            dcc.Link("← Back to Map", href="/")
        ])


# --- 5. Callbacks ---

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """
    Router callback to switch between the main page and detail pages.
    """
    if pathname and pathname.startswith("/detail/"):
        station_id = pathname.split("/")[-1]
        return layout_detail(station_id)
    return layout_index()


@app.callback(
    [Output('marker-layer', 'children'),
     Output('slider-output-container', 'children')],
    Input('month-slider', 'value')
)
def update_map_and_slider_label(selected_slider_index):
    """
    Updates the map markers and the text below the slider based on the selected month.
    """
    if df.empty or len(unique_year_months) == 0:
        return [], "Data not available"

    # Get the selected month-year period from the slider's index
    selected_period = unique_year_months[selected_slider_index]
    
    # Filter the dataframe for that specific month
    subset_df = df[df['DATE'].dt.to_period('M') == selected_period]

    if subset_df.empty:
        # Handle cases where a month might have no data for any station
        label_text = f"No data available for: {selected_period.strftime('%B %Y')}"
        return [], html.Span(label_text, style={'color':'black'})

    markers = []
    traffic_volume_explanation = "Traffic Volume represents the average number of vehicles counted over a 24-hour period (Monday-Sunday)."
    for _, row in subset_df.iterrows():
        # Use ensemble value if available (for future dates), otherwise use historical DTVMS
        display_value = row['DTVMS_ensemble'] if pd.notna(row['DTVMS_ensemble']) else row['DTVMS']
        # FIX: Ensure the protocol is included for an absolute URL
        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={row['LATITUDE']},{row['LONGITUDE']}"
        
        # Create a popup for each marker
        popup_content = html.Div([
            html.Strong(row['ZNAME']), html.Br(),
            f"Traffic Volume: {display_value:.0f}", html.Br(),
            f"District Code: {int(row['BEZIRK'])}", html.Br(),
            f"District Name: {row['BEZIRK_NAME']}", html.Br(),
            html.A("View on Google Maps", href=gmaps_link, target="_blank"), html.Br(),
            html.Hr(),
            html.P(traffic_volume_explanation, style={'fontSize': '0.8em'}),
            dcc.Link("Go to Details →", href=f"/detail/{row['ZNR']}")
        ])
        
        # Create the circle marker. Radius is scaled by traffic volume.
        markers.append(
            dl.CircleMarker(
                center=(row['LATITUDE'], row['LONGITUDE']),
                # Scale radius: base size + traffic contribution, with a max cap
                radius=min(8 + (display_value / 5000), 25),
                color="#007bff",
                fill=True,
                fillOpacity=0.7,
                children=[dl.Popup(popup_content)]
            )
        )
    
    label_text = f"Displaying data for: {selected_period.strftime('%B %Y')}"
    # Change color if the date is in the forecast period
    text_color = 'red' if selected_period.year >= 2025 else 'black'
    
    return markers, html.Span(label_text, style={'color':text_color})


# --- 6. Run the App ---
if __name__ == '__main__':
    # Setting debug=True allows for hot-reloading
    app.run(debug=True)
