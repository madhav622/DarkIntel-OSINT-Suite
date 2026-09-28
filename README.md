# 🛡️ DarkIntel OSINT Suite

An end-to-end Cyber Threat Intelligence (CTI) & Darkweb Scraper Suite built with Python and Streamlit.

## Features
- **Tor SOCKS5 Ingestion Engine**: Live `.onion` & Clearweb threat scraping via SOCKS5 proxy (`socks5h`).
- **Entity Extractor**: Regex-based extraction for Bitcoin/ETH/XMR wallets, PGP Public Keys, and GEO coordinates.
- **Harvested Identifiers DB**: SQLite-backed searchable database for extracted threat indicators.
- **GEO-INT Spatial Mapper**: Folium interactive map for tactical dead-drop tracking.
- **Actionable Intel Exporter**: PDF report generator for analysts.

## Setup & Run
1. Start Tor Daemon: `sudo systemctl restart tor`
2. Install Dependencies: `pip install streamlit requests pandas folium streamlit-folium reportlab urllib3`
3. Launch Suite: `streamlit run app.py`
