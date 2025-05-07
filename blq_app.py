import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Initialize the app
app = dash.Dash(__name__)
server = app.server
app.title = "25 Years at BLQ"

# Load data
df = pd.read_csv("consuntivo_bologna_total.csv")
df = df[df['Year'] < 2025]  # Exclude incomplete 2025 from display

# Add passengers per movement (efficiency proxy)
df['Passengers_per_Movement'] = df['Bologna_Passengers'] / df['Bologna_Movements']

# KPI mapping (label to column)
kpi_mapping = {
    "Passenger Traffic": "Bologna_Passengers",
    "Total Movements": "Bologna_Movements",
    "Cargo Tons": "Bologna_Cargo_Tons",
    "Avg Pre-Departure Delay per Flight": "AVG_DELAY_PER_FLIGHT",
    "CO₂ Emissions - Italy": "Annual_CO2_Emissions"
}

# Units for tooltip formatting
kpi_units = {
    "Passenger Traffic": "passengers",
    "Total Movements": "movements",
    "Cargo Tons": "tons",
    "Avg Pre-Departure Delay per Flight": "min/flight",
    "CO₂ Emissions - Italy": "tons CO₂"
}

# Normalize all KPIs and store original values
df_normalized = df.copy()
for label, column in kpi_mapping.items():
    max_value = df_normalized[column].max()
    df_normalized[label + "_normalized"] = df_normalized[column] / max_value

# Define key events to annotate
annotations = {
    2000: "Bologna: European Capital of Culture",
    2013: "High-speed rail station opens",
    2015: "The company is listed on the Milan Stock Exchange",
    2020: "Marconi Express & COVID lockdown",
    2023: "WHO ends pandemic state"
}

# Layout
app.layout = html.Div([
    html.Div([
        html.H1("25 Years at BLQ", style={"textAlign": "center", "marginBottom": "0"}),
        html.H4("Tracking air traffic, delays, and emissions (2000–2024)", 
                style={"textAlign": "center", "marginTop": "0", "color": "blue"})
    ], style={"padding": "40px", "backgroundColor": "#f9f9f9"}),


    html.Div([
        html.Label("Select year range:", style={"fontWeight": "bold", "marginBottom": "10px"}),
        html.Div([
            dcc.RangeSlider(
                id='year-slider',
                min=2000,
                max=2024,
                value=[2000, 2024],
                marks={str(year): str(year) for year in range(2000, 2025, 2)},
                step=1,
                allowCross=False,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={"marginBottom": "30px"}),

        html.Label("Select metrics to display:", style={"fontWeight": "bold", "marginBottom": "10px"}),
        dcc.Checklist(
            id='kpi-selector',
            options=[{"label": label, "value": label} for label in kpi_mapping.keys()],
            value=list(kpi_mapping.keys()),
            labelStyle={"display": "inline-block", "marginRight": "15px"},
            style={"marginBottom": "30px"}
        ),

        dcc.Graph(id='custom-kpi-chart'),
        html.Ul(id='annotation-list', style={"paddingTop": "20px", "fontSize": "0.9em", "color": "#555"}),
        html.P("Note: Pre-departured delay data from Eurocontrol is only available from 2016 onward.", style={"fontSize": "0.8em", "color": "gray", "paddingTop": "5px"}),
        html.Label("Select volume type:", style={"fontWeight": "bold", "marginBottom": "10px", "marginTop": "20px"}),
        dcc.RadioItems(
            id='volume-toggle',
            options=[
                {"label": "Passenger Traffic", "value": "Passenger"},
                {"label": "Cargo Tons", "value": "Cargo"}
            ],
            value="Passenger",
            labelStyle={"display": "inline-block", "marginRight": "20px"},
            style={"marginBottom": "20px"}
        ),

        html.Div([
            html.Div([
                dcc.Graph(id='volume-comparison')
            ], style={"width": "49%", "display": "inline-block"}),

            html.Div([
                dcc.Graph(id='co2-efficiency'),
                html.P("Note: Aviation-specific CO₂ data from Eurocontrol is only available from 2010 onward.", style={"fontSize": "0.8em", "color": "gray", "paddingTop": "5px", "textAlign": "center"})
            ], style={"width": "49%", "display": "inline-block", "verticalAlign": "top"})
        ], style={"paddingTop": "30px"}),

        html.Div([
            dcc.Graph(id='scatter-co2-vs-efficiency')
        ], style={"paddingTop": "50px"})
    ], style={"padding": "40px", "backgroundColor": "#f0f2f5"})
])

# Callback to update the main normalized line chart and annotations
@app.callback(
    Output('custom-kpi-chart', 'figure'),
    Output('annotation-list', 'children'),
    Input('kpi-selector', 'value'),
    Input('year-slider', 'value')
)
def update_chart(selected_kpis, selected_years):
    if not selected_kpis:
        return px.line(title="Please select at least one metric."), []

    filtered = df_normalized[(df_normalized['Year'] >= selected_years[0]) & (df_normalized['Year'] <= selected_years[1])]

    records = []
    for label in selected_kpis:
        for _, row in filtered.iterrows():
            records.append({
                "Year": row['Year'],
                "Metric": label,
                "Normalized Value": row[label + "_normalized"],
                "Real Value": row[kpi_mapping[label]],
                "Unit": kpi_units[label]
            })

    df_melted = pd.DataFrame(records)

    fig = px.line(
        df_melted,
        x='Year',
        y='Normalized Value',
        color='Metric',
        title='Normalized KPIs at Bologna Airport (2000–2024)',
        labels={"Normalized Value": "Normalized Scale (0–1)", "Metric": "Metric"},
        custom_data=["Real Value", "Unit"]
    )

    fig.update_traces(
        hovertemplate="%{x}<br>%{y:.2f} (normalized)<br>Value: %{customdata[0]:,.0f} %{customdata[1]}<extra></extra>"
    )
    fig.update_layout(margin={"l":40, "r":40, "t":60, "b":40})

    annotation_list = []
    for year, text in annotations.items():
        if selected_years[0] <= year <= selected_years[1]:
            fig.add_vline(x=year, line_width=1, line_dash="dash", line_color="gray")
            annotation_list.append(html.Li(f"{year}: {text}"))

    return fig, annotation_list

# Callback to update bar charts and scatter
@app.callback(
    Output('volume-comparison', 'figure'),
    Output('co2-efficiency', 'figure'),
    Output('scatter-co2-vs-efficiency', 'figure'),
    Input('year-slider', 'value'),
    Input('volume-toggle', 'value')
)
def update_bar_charts(year_range, volume_type):
    dff = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

    fig1 = go.Figure()
    if volume_type == 'Passenger':
        fig1.add_trace(go.Bar(x=dff['Year'], y=dff['Bologna_Passengers'], name='Bologna', marker_color='blue'))
        fig1.add_trace(go.Bar(x=dff['Year'], y=dff['National_Avg_Passengers'], name='Italy Avg', marker_color='orangered'))
        fig1.update_layout(title='Passenger Traffic: Bologna vs National Avg')
    else:
        fig1.add_trace(go.Bar(x=dff['Year'], y=dff['Bologna_Cargo_Tons'], name='Bologna', marker_color='blue'))
        fig1.add_trace(go.Bar(x=dff['Year'], y=dff['National_Avg_Cargo_Tons'], name='Italy Avg', marker_color='orangered'))
        fig1.update_layout(title='Cargo Tons: Bologna vs National Avg')

    fig1.update_layout(
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)'
        )
    )

    dff_filtered = dff[dff['Year'] >= 2010].copy()
    dff_filtered['CO2_per_Pax'] = dff_filtered['TA_CO2_Tons'] / dff_filtered['National_Avg_Passengers']
    fig2 = px.bar(dff_filtered, x='Year', y='CO2_per_Pax', title='CO₂ per Passenger (Aviation-Specific, National)')

    fig3 = px.scatter(
        dff_filtered,
        x='Passengers_per_Movement',
        y='CO2_per_Pax',
        hover_name='Year',
        trendline='ols',
        title='Load Efficiency vs CO₂ per Passenger (2010–2024)',
        labels={
            'Passengers_per_Movement': 'Passengers per Flight (Bologna)',
            'CO2_per_Pax': 'CO₂ per Passenger (tons)'
        }
    )

    return fig1, fig2, fig3

# Run server

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)

