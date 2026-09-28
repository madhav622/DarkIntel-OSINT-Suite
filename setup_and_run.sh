#!/bin/bash

echo "[+] Step 1: Installing Dependencies..."
pip install folium streamlit-folium reportlab pandas requests "requests[socks]" PySocks --break-system-packages > /dev/null 2>&1

echo "[+] Step 2: Restarting Tor Service..."
sudo service tor restart

echo "[+] Step 3: Setting Up Directory Structure..."
mkdir -p scraper parsers database data reports
touch scraper/__init__.py parsers/__init__.py database/__init__.py

echo "[+] Step 4: Writing Scraper Module..."
cat << 'PYEOF' > scraper/live_scraper.py
import requests

def scrape_onion_page(onion_url):
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'}
    
    if not onion_url.startswith(('http://', 'https://')):
        onion_url = 'http://' + onion_url
        
    try:
        response = requests.get(onion_url, proxies=proxies, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.text
    except Exception:
        pass
        
    try:
        if '.onion' not in onion_url:
            response = requests.get(onion_url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.text
    except Exception:
        pass
        
    return None
PYEOF

echo "[+] Step 5: Writing Parsers Module..."
cat << 'PYEOF' > parsers/data_extractor.py
import re

class DarknetIntelExtractor:
    def extract_pgp_keys(self, text):
        pgp_pattern = r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----'
        return re.findall(pgp_pattern, text)

    def extract_crypto_wallets(self, text):
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\bbc1[qzm3cjoy2526qch7w93deffzzpd52326w93def]{38,59}\b'
        xmr_pattern = r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'
        return {
            'btc': list(set(re.findall(btc_pattern, text))),
            'xmr': list(set(re.findall(xmr_pattern, text)))
        }

    def extract_geo_mentions(self, text):
        geo_keywords = ['dead drop', 'coordinates', 'latitude', 'drop zone', 'location', 'shipping']
        found = []
        for line in text.split('\n'):
            if any(kw in line.lower() for kw in geo_keywords):
                found.append(line.strip())
        return found
PYEOF

echo "[+] Step 6: Writing Database Manager Module..."
cat << 'PYEOF' > database/db_manager.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "darkintel.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendors (
        vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        alias TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendor_identifiers (
        identifier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        type TEXT,
        value TEXT,
        FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS dead_drops (
        drop_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        raw_location_text TEXT,
        latitude REAL,
        longitude REAL,
        country TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS raw_intel_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        market_or_forum TEXT,
        post_content TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
PYEOF

echo "[+] Step 7: Writing PDF Generator Module..."
cat << 'PYEOF' > reports/pdf_generator.py
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(metrics, logs, filename="reports/DarkIntel_Threat_Report.pdf"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#00e676'), spaceAfter=12)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1e222d'), spaceAfter=8)

    story.append(Paragraph("🕵️‍♂️ DarkIntel OSINT Suite - Threat Intelligence Report", title_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Executive Summary Metrics", heading_style))
    summary_data = [
        ["Target Vendors", "PGP Keys", "Crypto Wallets", "GEO Dead-Drops"],
        [str(metrics[0]), str(metrics[1]), str(metrics[2]), str(metrics[3])]
    ]
    t = Table(summary_data, colWidths=[120, 120, 120, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e222d')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#2d313e')),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Recent Scraped Target Logs", heading_style))
    log_data = [["Log ID", "Vendor ID", "Source / Onion URL", "Scraped At"]]
    for log in logs:
        log_data.append([str(log[0]), str(log[1]), str(log[2])[:30], str(log[3])])

    if len(log_data) == 1:
        log_data.append(["N/A", "N/A", "No ingestion logs recorded yet.", "N/A"])

    log_table = Table(log_data, colWidths=[60, 80, 200, 140])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d313e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(log_table)

    doc.build(story)
    return filename
PYEOF

echo "[+] Step 8: Writing Dashboard App (app.py)..."
cat << 'PYEOF' > app.py
import streamlit as st
import pandas as pd
import sqlite3
import os
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="DarkIntel OSINT Suite", page_icon="🕵️‍♂️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e6ed; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, #1e222d 0%, #14171f 100%); border: 1px solid #2d313e; border-radius: 10px; padding: 15px 20px; }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.9rem !important; font-weight: 600; }
    div[data-testid="stMetricValue"] { color: #00e676 !important; font-size: 1.8rem !important; font-weight: 700; }
    section[data-testid="stSidebar"] { background-color: #14171f; border-right: 1px solid #2d313e; }
    .intel-box { background: #1a1d26; border-left: 4px solid #00e676; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(90deg, #00c853 0%, #00e676 100%); color: #000000 !important; font-weight: 700 !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "darkintel.db")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH)

def fetch_metrics():
    conn = get_db_connection()
    if not conn:
        return 0, 0, 0, 0
    try:
        v_cnt = pd.read_sql_query("SELECT COUNT(*) as cnt FROM vendors", conn)['cnt'][0]
        p_cnt = pd.read_sql_query("SELECT COUNT(*) as cnt FROM vendor_identifiers WHERE type LIKE 'PGP%'", conn)['cnt'][0]
        c_cnt = pd.read_sql_query("SELECT COUNT(*) as cnt FROM vendor_identifiers WHERE type LIKE '%WALLET%'", conn)['cnt'][0]
        g_cnt = pd.read_sql_query("SELECT COUNT(*) as cnt FROM dead_drops", conn)['cnt'][0]
    except Exception:
        v_cnt, p_cnt, c_cnt, g_cnt = 0, 0, 0, 0
    finally:
        conn.close()
    return v_cnt, p_cnt, c_cnt, g_cnt

st.sidebar.markdown("## 🕵️‍♂️ DarkIntel Suite")
st.sidebar.markdown("<span style='color:#00e676; font-weight:bold;'>🟢 SOCKS5 PROXY: ACTIVE (9050)</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "NAVIGATION PANEL",
    ["📊 Dashboard Overview", "🌐 Target Ingestion Engine", "🔑 Harvested Identifiers", "📍 GEO-INT Intelligence", "📄 Actionable Intel Exporter"]
)

if page == "📊 Dashboard Overview":
    st.title("📊 Threat Intelligence Command Center")
    st.markdown("Real-time telemetry and scraped darknet entities.")
    v_cnt, p_cnt, c_cnt, g_cnt = fetch_metrics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Target Vendors", v_cnt)
    col2.metric("PGP Keys Harvested", p_cnt)
    col3.metric("Crypto Wallets", c_cnt)
    col4.metric("GEO Dead-Drops", g_cnt)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Recent Ingested Activity Logs")
    conn = get_db_connection()
    if conn:
        try:
            logs_df = pd.read_sql_query("SELECT log_id, vendor_id, market_or_forum, scraped_at FROM raw_intel_logs ORDER BY scraped_at DESC LIMIT 5", conn)
            st.dataframe(logs_df, use_container_width=True)
        except Exception:
            st.info("No activity recorded yet.")
        finally:
            conn.close()

elif page == "🌐 Target Ingestion Engine":
    st.title("🌐 Live Tor Target Ingestion")
    from scraper.live_scraper import scrape_onion_page
    from parsers.data_extractor import DarknetIntelExtractor
    
    extractor = DarknetIntelExtractor()
    target_url = st.text_input("Target .onion URL:", placeholder="https://httpbin.org/html")
    target_alias = st.text_input("Assign Vendor / Target Alias:", placeholder="Target_01")

    if st.button("🚀 Execute Ingestion"):
        if target_url and target_alias:
            with st.spinner("Fetching target content..."):
                html_content = scrape_onion_page(target_url)
                if html_content:
                    st.success("Scraped target successfully!")
                    pgp_keys = extractor.extract_pgp_keys(html_content)
                    wallets = extractor.extract_crypto_wallets(html_content)
                    
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT OR IGNORE INTO vendors (username, alias) VALUES (?, ?)", (target_alias, target_alias))
                        cursor.execute("SELECT vendor_id FROM vendors WHERE username = ?", (target_alias,))
                        vendor_id = cursor.fetchone()[0]
                        
                        for key in pgp_keys:
                            cursor.execute("INSERT INTO vendor_identifiers (vendor_id, type, value) VALUES (?, 'PGP_KEY', ?)", (vendor_id, key))
                        for btc in wallets['btc']:
                            cursor.execute("INSERT INTO vendor_identifiers (vendor_id, type, value) VALUES (?, 'BTC_WALLET', ?)", (vendor_id, btc))
                        for xmr in wallets['xmr']:
                            cursor.execute("INSERT INTO vendor_identifiers (vendor_id, type, value) VALUES (?, 'XMR_WALLET', ?)", (vendor_id, xmr))
                            
                        cursor.execute("INSERT INTO raw_intel_logs (vendor_id, market_or_forum, post_content) VALUES (?, ?, ?)", (vendor_id, target_url, html_content[:500]))
                        conn.commit()
                        conn.close()
                        st.info("Artifacts saved to SQLite Database!")
                else:
                    st.error("Failed to connect to target. Verify Tor proxy or URL.")
        else:
            st.warning("Please provide target URL and Alias.")

elif page == "🔑 Harvested Identifiers":
    st.title("🔑 Harvested Identifiers")
    conn = get_db_connection()
    if conn:
        try:
            entities_df = pd.read_sql_query("SELECT v.username as Target, i.type as Type, i.value as Artifact FROM vendor_identifiers i JOIN vendors v ON i.vendor_id = v.vendor_id", conn)
            st.dataframe(entities_df, use_container_width=True)
        except Exception:
            st.info("No identifiers in DB.")
        finally:
            conn.close()

elif page == "📍 GEO-INT Intelligence":
    st.title("📍 GEO-INT Mapping")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=4, tiles="CartoDB dark_matter")
    folium.Marker([51.5074, -0.1278], popup="Sample Target Location", icon=folium.Icon(color="green")).add_to(m)
    st_folium(m, width=1100, height=500)

elif page == "📄 Actionable Intel Exporter":
    st.title("📄 Actionable Intel Exporter")
    st.markdown("<div class='intel-box'>Export complete Dark Web threat landscape into an executive PDF report.</div>", unsafe_allow_html=True)
    
    if st.button("🔴 Generate Executive PDF Report"):
        from reports.pdf_generator import generate_pdf_report
        conn = get_db_connection()
        logs = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT log_id, vendor_id, market_or_forum, scraped_at FROM raw_intel_logs ORDER BY scraped_at DESC LIMIT 10")
                logs = cursor.fetchall()
            except Exception:
                pass
            finally:
                conn.close()

        v_cnt, p_cnt, c_cnt, g_cnt = fetch_metrics()
        pdf_path = generate_pdf_report((v_cnt, p_cnt, c_cnt, g_cnt), logs)

        with open(pdf_path, "rb") as f:
            st.download_button(label="📥 Download Threat Intelligence Report (.PDF)", data=f, file_name="DarkIntel_Threat_Report.pdf", mime="application/pdf")
        st.success("PDF Report generated successfully!")
PYEOF

echo "[+] Step 9: Initializing Database..."
python3 database/db_manager.py

echo "[+] Step 10: Launching Dashboard..."
python3 -m streamlit run app.py
