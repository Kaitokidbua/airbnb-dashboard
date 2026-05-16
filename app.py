import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import numpy as np

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Airbnb NYC · Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; font-weight: 800; }

.block-container { padding: 2rem 3rem; }

.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(255,90,95,0.3);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    color: white;
}
.metric-card .value {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #FF5A5F;
}
.metric-card .label {
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    color: #aaa;
    text-transform: uppercase;
    margin-top: 4px;
}

.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #FF5A5F;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.8rem;
    border-bottom: 2px solid rgba(255,90,95,0.2);
    padding-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MongoDB connection (using Streamlit Secrets)
# ─────────────────────────────────────────────
@st.cache_resource
def get_mongo_client():
    """Connect to MongoDB using credentials from st.secrets (never hardcoded)."""
    uri = st.secrets["mongodb"]["uri"]
    return MongoClient(uri)

@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    """Load Airbnb data from MongoDB and cache for 1 hour."""
    client = get_mongo_client()
    db = client[st.secrets["mongodb"]["db_name"]]
    collection = db[st.secrets["mongodb"]["collection"]]

    cursor = collection.find(
        {},
        {
            "_id": 0,
            "NAME": 1,
            "neighbourhood group": 1,
            "neighbourhood": 1,
            "lat": 1,
            "long": 1,
            "room type": 1,
            "price": 1,
            "minimum nights": 1,
            "number of reviews": 1,
            "reviews per month": 1,
            "calculated host listings count": 1,
            "availability 365": 1,
            "Construction year": 1,
            "service fee": 1,
            "house_rules": 1,
            "cancellation_policy": 1,
            "instant_bookable": 1,
        },
        limit=50000,
    )
    df = pd.DataFrame(list(cursor))
    return df

# ─────────────────────────────────────────────
# Data cleaning
# ─────────────────────────────────────────────
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Rename for convenience
    rename_map = {
        "neighbourhood group": "borough",
        "room type": "room_type",
        "minimum nights": "min_nights",
        "number of reviews": "num_reviews",
        "reviews per month": "reviews_pm",
        "calculated host listings count": "host_listings",
        "availability 365": "availability",
        "Construction year": "construction_year",
        "service fee": "service_fee",
    }
    df.rename(columns=rename_map, inplace=True)

    # Clean price
    for col in ["price", "service_fee"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[\$,]", "", regex=True)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["price"].between(10, 2000)]
    df = df.dropna(subset=["lat", "long", "borough", "room_type"])
    return df

# ─────────────────────────────────────────────
# App layout
# ─────────────────────────────────────────────
st.markdown("## 🏠 Airbnb NYC · Open Data Dashboard")
st.markdown("Explore listing data loaded from **MongoDB Atlas** — credentials stored securely via Streamlit Secrets.")

try:
    raw_df = load_data()
    df = clean_data(raw_df)
except Exception as e:
    st.error(f"❌ Could not connect to MongoDB: {e}")
    st.info("Make sure `.streamlit/secrets.toml` or Streamlit Cloud secrets are configured correctly.")
    st.stop()

# ─────────────────────────────────────────────
# Sidebar filters
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔎 Filters")

    boroughs = ["All"] + sorted(df["borough"].dropna().unique().tolist())
    selected_borough = st.selectbox("Borough", boroughs)

    room_types = ["All"] + sorted(df["room_type"].dropna().unique().tolist())
    selected_room = st.selectbox("Room Type", room_types)

    price_min, price_max = int(df["price"].min()), int(df["price"].max())
    price_range = st.slider("Price Range ($)", price_min, min(price_max, 2000), (50, 500))

    min_reviews = st.slider("Minimum Reviews", 0, 200, 0)

# ─────────────────────────────────────────────
# Filter data
# ─────────────────────────────────────────────
fdf = df.copy()
if selected_borough != "All":
    fdf = fdf[fdf["borough"] == selected_borough]
if selected_room != "All":
    fdf = fdf[fdf["room_type"] == selected_room]
fdf = fdf[fdf["price"].between(price_range[0], price_range[1])]
fdf = fdf[fdf["num_reviews"] >= min_reviews]

# ─────────────────────────────────────────────
# KPI Row
# ─────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (f"{len(fdf):,}", "Total Listings"),
    (f"${fdf['price'].mean():.0f}", "Avg Price / Night"),
    (f"${fdf['price'].median():.0f}", "Median Price"),
    (f"{fdf['num_reviews'].sum():,}", "Total Reviews"),
    (f"{fdf['availability'].mean():.0f} days", "Avg Availability"),
]
for col, (val, lbl) in zip([c1, c2, c3, c4, c5], kpis):
    col.markdown(
        f'<div class="metric-card"><div class="value">{val}</div><div class="label">{lbl}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Row 1: Map + Room Type Donut
# ─────────────────────────────────────────────
col_map, col_donut = st.columns([2, 1])

with col_map:
    st.markdown('<div class="section-header">📍 Listing Locations</div>', unsafe_allow_html=True)
    map_sample = fdf.sample(min(5000, len(fdf)), random_state=42) if len(fdf) > 5000 else fdf
    fig_map = px.scatter_mapbox(
        map_sample,
        lat="lat", lon="long",
        color="room_type",
        hover_name="NAME",
        hover_data={"price": True, "borough": True, "lat": False, "long": False},
        color_discrete_sequence=px.colors.qualitative.Bold,
        zoom=10,
        height=420,
        mapbox_style="carto-darkmatter",
        opacity=0.7,
    )
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_donut:
    st.markdown('<div class="section-header">🛏 Room Type Split</div>', unsafe_allow_html=True)
    room_counts = fdf["room_type"].value_counts().reset_index()
    room_counts.columns = ["room_type", "count"]
    fig_donut = px.pie(
        room_counts, names="room_type", values="count",
        hole=0.55,
        color_discrete_sequence=["#FF5A5F", "#00A699", "#FC642D", "#484848"],
        height=420,
    )
    fig_donut.update_traces(textposition="outside", textinfo="percent+label")
    fig_donut.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ─────────────────────────────────────────────
# Row 2: Price Distribution + Borough Avg Price
# ─────────────────────────────────────────────
col_hist, col_bar = st.columns(2)

with col_hist:
    st.markdown('<div class="section-header">💰 Price Distribution</div>', unsafe_allow_html=True)
    fig_hist = px.histogram(
        fdf[fdf["price"] <= 600], x="price", nbins=60,
        color_discrete_sequence=["#FF5A5F"],
        height=320,
    )
    fig_hist.update_layout(
        bargap=0.05,
        xaxis_title="Price per Night ($)",
        yaxis_title="Count",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with col_bar:
    st.markdown('<div class="section-header">🗺 Avg Price by Borough</div>', unsafe_allow_html=True)
    borough_price = (
        fdf.groupby("borough")["price"]
        .mean()
        .reset_index()
        .sort_values("price", ascending=True)
    )
    fig_bar = px.bar(
        borough_price, x="price", y="borough", orientation="h",
        color="price",
        color_continuous_scale=["#00A699", "#FF5A5F"],
        height=320,
        text=borough_price["price"].map(lambda v: f"${v:.0f}"),
    )
    fig_bar.update_layout(
        xaxis_title="Avg Price ($)",
        yaxis_title="",
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

# ─────────────────────────────────────────────
# Row 3: Reviews vs Price Scatter + Availability Box
# ─────────────────────────────────────────────
col_scatter, col_box = st.columns(2)

with col_scatter:
    st.markdown('<div class="section-header">⭐ Reviews vs Price</div>', unsafe_allow_html=True)
    scatter_df = fdf[fdf["num_reviews"] > 0].sample(min(3000, len(fdf)), random_state=1)
    fig_scatter = px.scatter(
        scatter_df, x="price", y="num_reviews",
        color="room_type",
        opacity=0.5,
        color_discrete_sequence=px.colors.qualitative.Bold,
        height=300,
        trendline="lowess",
        trendline_scope="overall",
        trendline_color_override="#ffffff",
    )
    fig_scatter.update_layout(
        xaxis_title="Price ($)", yaxis_title="Number of Reviews",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_box:
    st.markdown('<div class="section-header">📅 Availability by Borough</div>', unsafe_allow_html=True)
    fig_box = px.box(
        fdf, x="borough", y="availability",
        color="borough",
        color_discrete_sequence=px.colors.qualitative.Bold,
        height=300,
    )
    fig_box.update_layout(
        showlegend=False,
        xaxis_title="", yaxis_title="Days Available / Year",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ─────────────────────────────────────────────
# Row 4: Top Neighbourhoods Table
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🏘 Top 15 Neighbourhoods by Avg Price</div>', unsafe_allow_html=True)
top_hoods = (
    fdf.groupby(["borough", "neighbourhood"])
    .agg(
        avg_price=("price", "mean"),
        listings=("price", "count"),
        avg_reviews=("num_reviews", "mean"),
    )
    .reset_index()
    .sort_values("avg_price", ascending=False)
    .head(15)
)
top_hoods["avg_price"] = top_hoods["avg_price"].map("${:.0f}".format)
top_hoods["avg_reviews"] = top_hoods["avg_reviews"].map("{:.1f}".format)
st.dataframe(
    top_hoods.rename(columns={
        "borough": "Borough", "neighbourhood": "Neighbourhood",
        "avg_price": "Avg Price", "listings": "Listings", "avg_reviews": "Avg Reviews"
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Data source: Kaggle · arianazmoudeh/airbnbopendata · Stored in MongoDB Atlas")
