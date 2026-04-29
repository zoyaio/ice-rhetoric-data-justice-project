import pandas as pd
import folium
from folium.plugins import HeatMap
from branca.element import MacroElement
from jinja2 import Template as JinjaTemplate
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, render_template, request
from data import load_data, load_arrests, load_narratives, DATASETS

class ClickableMarker(MacroElement):
    def __init__(self, lat, lon, label, section, dest='/narratives-left-out'):
        super().__init__()
        self._name = 'ClickableMarker'
        self._template = JinjaTemplate("""
            {% macro script(this, kwargs) %}
            L.circleMarker(
                [{{ this.lat }}, {{ this.lon }}],
                {radius: 8, color: '#0055FF', fillColor: 'transparent', weight: 2}
            ).addTo({{ this._parent.get_name() }})
             .bindTooltip('{{ this.label }} — click to explore')
             .on('click', function() {
                 window.top.location.href = '{{ this.dest }}#{{ this.section }}';
             });
            {% endmacro %}
        """)
        self.lat = lat
        self.lon = lon
        self.label = label
        self.section = section
        self.dest = dest

app = Flask(__name__)
data = load_data()
arrests = load_arrests()
narratives = load_narratives()

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
        color_continuous_scale="Reds",
        labels={"count": "Arrests"},
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)

def build_choropleth(df: pd.DataFrame) -> str:
    state_counts = (
        df.groupby("adm1_code")
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
        color_continuous_scale="Reds",
        labels={"count": "Article Mentions"},
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn", div_id="articles-choropleth")

def build_heatmap(df: pd.DataFrame) -> str:
    state_coords = df[df["location_type"] == 2][["lat", "lon"]].values.tolist()
    city_coords  = df[df["location_type"] == 3][["lat", "lon"]].values.tolist()
    m = folium.Map(location=[39.5, -98.5], zoom_start=4, tiles="CartoDB positron")
    HeatMap(state_coords, radius=15, blur=10).add_to(m)
    HeatMap(city_coords,  radius=6,  blur=8).add_to(m)
    heatmap_cities = {
        'New York City': (40.7128, -74.0060, 'section-new-york-city'),
        'Long Beach':    (33.7701, -118.1937, 'section-long-beach'),
        'Fresno':        (36.7378, -119.7871, 'section-fresno'),
        'Minneapolis':   (44.9778, -93.2650,  'section-minneapolis'),
    }
    for label, (lat, lon, section) in heatmap_cities.items():
        ClickableMarker(lat, lon, label, section, dest='/media-desensitization').add_to(m)
    return m._repr_html_()

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

    choropleth_html = build_choropleth(df)
    arrests_choropleth_html = build_arrests_choropleth(start_date_str, end_date_str)
    dataset_options = {k: v["label"] for k, v in DATASETS.items()}

    full_df = data[dataset_key]
    min_date = min(full_df["DATE"].min(), arrests["date"].min()).strftime("%Y-%m-%d")
    max_date = max(full_df["DATE"].max(), arrests["date"].max()).strftime("%Y-%m-%d")

    return render_template(
        'media_representation.html',
        choropleth=choropleth_html,
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
    full_df = data['dhs_migration']
    heatmap_html = build_heatmap(full_df)
    return render_template('media_desensitization.html', heatmap=heatmap_html)

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
        color_continuous_scale="Reds",
        labels={"count": "Article Mentions"},
    )
    cities = {
        'New York City': (40.7128, -74.0060),
        'Long Beach':    (33.7701, -118.1937),
        'Sacramento':    (38.5816, -121.4944),
        'Los Angeles':   (34.0522, -118.2437),
        'Fresno':        (36.7378, -119.7871),
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
            line=dict(color='#2a9d2a', width=2),
        ),
        hovertemplate='%{customdata} — click to explore<extra></extra>',
        showlegend=False,
    ))
    choropleth_html = fig.to_html(full_html=False, include_plotlyjs="cdn", div_id="narratives-choropleth")
    return render_template('narratives_left_out.html', choropleth=choropleth_html, narratives=narratives)

if __name__ == '__main__':
    app.run(debug=True)
