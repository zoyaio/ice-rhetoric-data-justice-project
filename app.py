import pandas as pd
import folium
from folium.plugins import HeatMap
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, render_template, request
from data import load_data, load_arrests, DATASETS

app = Flask(__name__)
data = load_data()
arrests = load_arrests()

def build_arrests_choropleth(start_date_str: str, end_date_str: str) -> str:
    df = arrests.copy()
    if start_date_str:
        df = df[df["date"] >= pd.Timestamp(start_date_str)]
    if end_date_str:
        df = df[df["date"] <= pd.Timestamp(end_date_str)]
    state_counts = df.groupby("state_code").size().reset_index(name="count")
    fig = px.choropleth(
        state_counts,
        locations="state_code",
        locationmode="USA-states",
        scope="usa",
        color="count",
        color_continuous_scale="Viridis_r",
        labels={"count": "Arrests"},
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)

def build_plots(df: pd.DataFrame):
    state_counts = (
        df.groupby("adm1_code")
        .size()
        .reset_index(name="count")
    )
    state_counts["state_code"] = state_counts["adm1_code"].str[2:]
    choropleth_fig = px.choropleth(
        state_counts,
        locations="state_code",
        locationmode="USA-states",
        scope="usa",
        color="count",
        color_continuous_scale="Viridis_r",
        labels={"count": "Article Mentions"},
    )
    choropleth_html = choropleth_fig.to_html(full_html=False, include_plotlyjs="cdn", div_id="articles-choropleth")

    state_coords = df[df["location_type"] == 2][["lat", "lon"]].values.tolist()
    city_coords  = df[df["location_type"] == 3][["lat", "lon"]].values.tolist()
    m = folium.Map(location=[39.5, -98.5], zoom_start=4, tiles="CartoDB positron")
    HeatMap(state_coords, radius=15, blur=10).add_to(m)
    HeatMap(city_coords,  radius=6,  blur=8).add_to(m)
    heatmap_html = m._repr_html_()

    return choropleth_html, heatmap_html

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/media-representation', methods=['GET', 'POST'])
def media_representation():
    dataset_key    = request.form.get('dataset', 'dhs_migration')
    start_date_str = request.form.get('start_date', '')
    end_date_str   = request.form.get('end_date', '')

    df = data[dataset_key].copy()
    if start_date_str:
        df = df[df["DATE"] >= pd.Timestamp(start_date_str)]
    if end_date_str:
        df = df[df["DATE"] <= pd.Timestamp(end_date_str)]

    choropleth_html, heatmap_html = build_plots(df)
    arrests_choropleth_html = build_arrests_choropleth(start_date_str, end_date_str)
    dataset_options = {k: v["label"] for k, v in DATASETS.items()}

    full_df = data[dataset_key]
    min_date = min(full_df["DATE"].min(), arrests["date"].min()).strftime("%Y-%m-%d")
    max_date = max(full_df["DATE"].max(), arrests["date"].max()).strftime("%Y-%m-%d")

    return render_template(
        'media_representation.html',
        choropleth=choropleth_html,
        heatmap=heatmap_html,
        arrests_choropleth=arrests_choropleth_html,
        dataset_options=dataset_options,
        selected_dataset=dataset_key,
        start_date=start_date_str,
        end_date=end_date_str,
        min_date=min_date,
        max_date=max_date,
    )

@app.route('/media-desensitization')
def media_desensitization():
    return render_template('media_desensitization.html')

@app.route('/narratives-left-out')
def narratives_left_out():
    full_df = data['dhs_migration']
    state_counts = (
        full_df.groupby("adm1_code")
        .size()
        .reset_index(name="count")
    )
    state_counts["state_code"] = state_counts["adm1_code"].str[2:]
    fig = px.choropleth(
        state_counts,
        locations="state_code",
        locationmode="USA-states",
        scope="usa",
        color="count",
        color_continuous_scale="Viridis_r",
        labels={"count": "Article Mentions"},
    )
    cities = {
        'New York City': (40.7128, -74.0060),
        'Long Beach':    (33.7701, -118.1937),
        'Sacramento':    (38.5816, -121.4944),
        'Los Angeles':   (34.0522, -118.2437),
    }
    fig.add_trace(go.Scattergeo(
        lat=[c[0] for c in cities.values()],
        lon=[c[1] for c in cities.values()],
        text=list(cities.keys()),
        customdata=list(cities.keys()),
        mode='markers',
        marker=dict(
            size=10,
            color='rgba(0,0,0,0)',
            line=dict(color='#0055FF', width=2),
        ),
        hovertemplate='%{customdata} — click to explore<extra></extra>',
        showlegend=False,
    ))
    choropleth_html = fig.to_html(full_html=False, include_plotlyjs="cdn", div_id="narratives-choropleth")
    return render_template('narratives_left_out.html', choropleth=choropleth_html)

if __name__ == '__main__':
    app.run(debug=True)
