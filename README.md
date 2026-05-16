# 🏠 Airbnb NYC Dashboard

Streamlit dashboard visualising Airbnb NYC listings stored in MongoDB Atlas.  
**No credentials are hard-coded or committed to the repository.**

---

## Project Structure

```
airbnb_dashboard/
├── app.py                     # Main Streamlit application
├── load_to_mongodb.py         # One-time CSV → MongoDB loader
├── requirements.txt
├── .env.example               # Template (copy → .env, fill in your URI)
├── .gitignore                 # Blocks .env & secrets.toml from git
└── .streamlit/
    └── secrets.toml           # LOCAL ONLY — never committed
```

---

## 🔐 How secrets are kept safe

| Environment | Where credentials live | Committed to git? |
|---|---|---|
| Local dev | `.streamlit/secrets.toml` | ❌ blocked by `.gitignore` |
| Streamlit Cloud | App Settings → **Secrets** panel | ❌ stored encrypted by Streamlit |
| Loader script | `.env` file | ❌ blocked by `.gitignore` |

The app accesses credentials only via `st.secrets["mongodb"]["uri"]`.  
If MongoDB is unreachable, it falls back to the local CSV automatically.

---

## 🚀 Setup

### 1. Clone and install

```bash
git clone https://github.com/<you>/airbnb-dashboard.git
cd airbnb-dashboard
pip install -r requirements.txt
```

### 2. Create your secrets file (local)

```bash
cp .env.example .env          # for the loader script
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# → fill in your Atlas URI in both files
```

### 3. Load data into MongoDB Atlas (run once)

```bash
python load_to_mongodb.py
```

### 4. Run Streamlit locally

```bash
streamlit run app.py
```

---

## ☁️ Deploy to Streamlit Cloud

1. Push this repo to GitHub (**do NOT push `.env` or `secrets.toml`**)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo → `app.py`
4. Click **Advanced settings → Secrets** and paste:

```toml
[mongodb]
uri        = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/"
database   = "airbnb_db"
collection = "listings"
```

5. Deploy ✅

---

## 📊 Dashboard Features

| Section | Chart type | Insight |
|---|---|---|
| KPI row | Metrics | Quick summary stats |
| Price by Borough & Room Type | Grouped bar | Cross-dimensional pricing |
| Room Type Share | Donut pie | Listing mix |
| Geo Map | Scatter Mapbox | Spatial price distribution |
| Price Distribution | Box plot | Spread & outliers per borough |
| Availability vs Price | Scatter | Supply–demand relationship |
| Top 15 Neighbourhoods | Horizontal bar | Most expensive areas |
| Construction Year Trend | Line chart | Borough growth over time |
| Raw Data | Expandable table | Drill-down inspection |
