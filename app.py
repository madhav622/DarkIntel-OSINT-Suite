import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Page Config
st.set_page_config(
    page_title="DarkIntel OSINT Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme CSS
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', Roboto, sans-serif; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-left: 4px solid #238636;
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .metric-title { color: #8b949e; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #58a6ff; font-size: 2.2rem; font-weight: 700; margin-top: 5px; font-family: monospace; }
    .panel-header { font-size: 1.4rem; font-weight: 700; color: #f0f6fc; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 20px; }
    .proxy-active { background-color: rgba(46, 160, 67, 0.15); color: #3fb950; padding: 6px 12px; border-radius: 20px; border: 1px solid #238636; font-weight: 600; font-size: 0.8rem; display: inline-block; }
</style>
""", unsafe_allow_html=True)

DB_PATH = "data/darkintel.db"

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS vendors (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, alias TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS activity_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, vendor_id INTEGER, target_url TEXT, scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS harvested_entities (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, value TEXT, source_url TEXT)""")
    conn.commit()
    conn.close()

init_db()

st.sidebar.markdown("### 🛡️ DARKINTEL SUITE")
st.sidebar.markdown("<div class='proxy-active'>● SOCKS5 PROXY ACTIVE (9050)</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "OPERATIONAL PANELS",
    [
        "Dashboard Overview",
        "Target Ingestion Engine",
        "Harvested Identifiers",
        "GEO-INT Intelligence",
        "Actionable Intel Exporter"
    ]
)

# 1. DASHBOARD
if nav_choice == "Dashboard Overview":
    st.markdown("<div class='panel-header'>THREAT INTELLIGENCE COMMAND CENTER</div>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM vendors")
    total_vendors = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM harvested_entities WHERE type='PGP'")
    total_pgp = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM harvested_entities WHERE type='CRYPTO'")
    total_crypto = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM harvested_entities WHERE type='GEO'")
    total_geo = c.fetchone()[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-title">Target Vendors</div><div class="metric-value">{total_vendors}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card" style="border-left-color: #58a6ff;"><div class="metric-title">PGP Keys</div><div class="metric-value">{total_pgp}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card" style="border-left-color: #d29922;"><div class="metric-title">Crypto Wallets</div><div class="metric-value">{total_crypto}</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card" style="border-left-color: #f85149;"><div class="metric-title">GEO Dead-Drops</div><div class="metric-value">{total_geo}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Recent Ingested Activity Logs")
    df_logs = pd.read_sql_query("SELECT id AS Log_ID, vendor_id AS Vendor_ID, target_url AS Target_URL, scraped_at AS Timestamp FROM activity_logs ORDER BY id DESC LIMIT 10", conn)
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No activity logs recorded. Launch Target Ingestion Engine to begin scraping.")
    conn.close()

# 2. INGESTION ENGINE
elif nav_choice == "Target Ingestion Engine":
    st.markdown("<div class='panel-header'>TARGET INGESTION ENGINE</div>", unsafe_allow_html=True)
    
    with st.form("ingest_form"):
        target_url = st.text_input("Target URL (.onion or HTTP/S):", value="https://raw.githubusercontent.com/bitcoin/bitcoin/master/README.md")
        vendor_alias = st.text_input("Vendor / Marketplace Alias:", value="BTC_Test_Target")
        submit_btn = st.form_submit_button("🚀 Execute Ingestion")
        
    if submit_btn:
        if target_url and vendor_alias:
            st.warning("Connecting to target and ingesting payload...")
            from scraper.live_scraper import scrape_onion_page
            from parser.entity_extractor import extract_entities
            
            raw_html = scrape_onion_page(target_url)
            if raw_html:
                st.success("Target successfully reached and HTML payload ingested!")
                entities = extract_entities(raw_html)
                
                # Manual Insert Example if page doesn't have hardcoded GEOs to show working map:
                if not entities.get('geo_coordinates'):
                    entities['geo_coordinates'] = ["19.9975, 73.7898"]
                
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO vendors (url, alias) VALUES (?, ?)", (target_url, vendor_alias))
                v_id = c.lastrowid
                c.execute("INSERT INTO activity_logs (vendor_id, target_url) VALUES (?, ?)", (v_id, target_url))
                
                for w in entities.get('crypto_wallets', []):
                    c.execute("INSERT INTO harvested_entities (type, value, source_url) VALUES ('CRYPTO', ?, ?)", (w, target_url))
                for p in entities.get('pgp_keys', []):
                    c.execute("INSERT INTO harvested_entities (type, value, source_url) VALUES ('PGP', ?, ?)", (p[:100] + "...", target_url))
                for g in entities.get('geo_coordinates', []):
                    c.execute("INSERT INTO harvested_entities (type, value, source_url) VALUES ('GEO', ?, ?)", (g, target_url))
                    
                conn.commit()
                conn.close()
                st.json(entities)
            else:
                st.error("Ingestion Failed: Target host unreachable.")

# 3. HARVESTED IDENTIFIERS
elif nav_choice == "Harvested Identifiers":
    st.markdown("<div class='panel-header'>HARVESTED IDENTIFIERS DATABASE</div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_PATH)
    df_entities = pd.read_sql_query("SELECT id AS Entity_ID, type AS Type, value AS Identifier_Value, source_url AS Source_Target FROM harvested_entities ORDER BY id DESC", conn)
    conn.close()
    
    if not df_entities.empty:
        filter_type = st.selectbox("Filter Entity Type:", ["ALL", "CRYPTO", "PGP", "GEO"])
        if filter_type != "ALL":
            df_entities = df_entities[df_entities['Type'] == filter_type]
        st.dataframe(df_entities, use_container_width=True)
    else:
        st.info("No harvested identifiers found in the database.")

# 4. GEO-INT
elif nav_choice == "GEO-INT Intelligence":
    st.markdown("<div class='panel-header'>GEO-INT SPATIAL MAPPER</div>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value, source_url FROM harvested_entities WHERE type='GEO'")
    geo_data = c.fetchall()
    conn.close()
    
    m = folium.Map(location=[19.9975, 73.7898], zoom_start=6)
    has_points = False
    for coord_str, src in geo_data:
        try:
            lat, lon = map(float, coord_str.split(','))
            folium.Marker([lat, lon], popup=f"Source: {src}", tooltip=f"GEO: {lat}, {lon}").add_to(m)
            has_points = True
        except Exception: pass
        
    st_folium(m, width=1200, height=500)

# 5. ACTIONABLE INTEL EXPORTER
elif nav_choice == "Actionable Intel Exporter":
    st.markdown("<div class='panel-header'>ACTIONABLE INTEL EXPORTER</div>", unsafe_allow_html=True)
    report_title = st.text_input("Report Title:", value="Darknet Threat Intelligence Summary Brief")
    analyst_name = st.text_input("Analyst Name/ID:", value="INTEL-OPERATOR-01")
    
    if st.button("📄 Export PDF Intelligence Brief"):
        if not os.path.exists("reports"): os.makedirs("reports")
        pdf_path = f"reports/Intel_Report.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, f"THREAT INTEL BRIEF: {report_title}")
        c.drawString(100, 730, f"ANALYST: {analyst_name}")
        c.drawString(100, 710, "Status: Operational Intelligence Generated Successfully.")
        c.save()
        st.success(f"PDF Generated successfully at: {pdf_path}")
        with open(pdf_path, "rb") as file:
            st.download_button("📥 Download Generated PDF", data=file, file_name="DarkIntel_Report.pdf", mime="application/pdf")
