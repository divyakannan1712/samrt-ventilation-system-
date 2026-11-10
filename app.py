import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="Smart Ventilation | IoT Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme ----------
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #0b1220; color: #e5edf5; }
[data-testid="stSidebar"] { background: #101b2b; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
.hero {
    padding: 1.35rem 1.5rem; border: 1px solid #254338;
    border-radius: 18px; background: linear-gradient(120deg,#102c27,#142235);
    margin-bottom: 1.2rem;
}
.hero h1 { margin: 0; color: #e8fff5; font-size: 2rem; }
.hero p { color: #a9c8bd; margin: .35rem 0 0 0; }
.metric {
    background: #121f30; border: 1px solid #26394c; border-radius: 14px;
    padding: 1rem 1.1rem; min-height: 112px;
}
.metric-label { color: #9eb2c5; font-size: .88rem; }
.metric-value { color: #f1f7fb; font-size: 1.75rem; font-weight: 700; margin-top: .25rem; }
.metric-note { color: #8ca49a; font-size: .78rem; margin-top: .2rem; }
.status-pill {
    display:inline-block; border-radius:999px; padding:.25rem .7rem;
    background:#183b30; color:#9af0c5; font-size:.82rem;
}
.small-muted { color:#91a4b8; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

# ---------- API helpers ----------
default_api = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
if "api_url" not in st.session_state:
    st.session_state.api_url = default_api

def api_get(path, timeout=5):
    base = st.session_state.api_url.strip().rstrip("/")
    if not base:
        raise ValueError("Enter the backend API address.")
    response = requests.get(base + path, timeout=timeout)
    response.raise_for_status()
    return response.json()

def fmt(value, suffix=""):
    if value is None:
        return "—"
    try:
        return f"{float(value):.1f}{suffix}"
    except (TypeError, ValueError):
        return f"{value}{suffix}"

def metric_card(label, value, note=""):
    st.markdown(
        f'<div class="metric"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🌿 SMART VENTILATION")
    st.caption("IoT monitoring and indoor air guidance")
    st.markdown("---")
    st.markdown("### BACKEND CONNECTION")
    st.text_input("API address", key="api_url", help="Local example: http://127.0.0.1:8000 | Hosted example: https://your-service.onrender.com")
    history_limit = st.selectbox("History records", [25, 50, 100, 250, 500], index=2)
    if st.button("↻ Refresh dashboard", use_container_width=True):
        st.rerun()
    st.markdown("---")
    st.caption("ESP32 → FastAPI → SQLite → Streamlit")
    st.caption("Use the public backend URL when this dashboard is hosted.")

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>🌿 Smart Ventilation Dashboard</h1>
  <p>Real-time environmental monitoring · Air quality · Temperature · Motion · Fan status</p>
</div>
""", unsafe_allow_html=True)

# ---------- Fetch ----------
health = None
latest_response = {"available": False, "data": None}
history_response = {"data": []}
api_error = None

try:
    health = api_get("/api/health")
    latest_response = api_get("/api/latest")
    history_response = api_get(f"/api/history?limit={history_limit}")
except requests.RequestException as exc:
    api_error = f"Cannot reach backend: {exc}"
except Exception as exc:
    api_error = str(exc)

if api_error:
    st.error("Backend connection failed. " + api_error)
    st.info("Check that the FastAPI backend is running and that the API address is correct. A hosted Streamlit website cannot use 127.0.0.1 to reach a backend running on your phone or laptop.")
    st.code("python -m uvicorn backend:app --host 0.0.0.0 --port 8000", language="bash")
    st.stop()

data = latest_response.get("data") if latest_response.get("available") else None
history = history_response.get("data", []) or []

# ---------- Connection status ----------
col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    st.markdown('<span class="status-pill">● Backend connected</span>', unsafe_allow_html=True)
with col_b:
    st.markdown(
        '<span class="status-pill">● ESP32 data received</span>' if data
        else '<span class="status-pill" style="background:#49351c;color:#ffd28a">● Waiting for ESP32</span>',
        unsafe_allow_html=True
    )
with col_c:
    st.markdown(f'<div class="small-muted">API: {st.session_state.api_url}</div>', unsafe_allow_html=True)

if not data:
    st.warning("Backend is connected, but no ESP32 readings have arrived yet. Power the ESP32 and make sure it is sending POST requests to /api/telemetry.")
    st.stop()

# ---------- Main metrics ----------
st.markdown("### LIVE SENSOR READINGS")
m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card("Air quality · MQ135", fmt(data.get("mq135")), "Raw analog sensor value")
with m2:
    metric_card("Temperature", fmt(data.get("temperature"), " °C"), "DHT11")
with m3:
    metric_card("Humidity", fmt(data.get("humidity"), " %"), "DHT11")
with m4:
    metric_card("Movement", "Detected" if data.get("pir_motion") else "No motion", "PIR sensor")

st.markdown("### SYSTEM STATUS")
s1, s2, s3, s4 = st.columns(4)
with s1:
    metric_card("Operating mode", str(data.get("mode") or "—").title(), "Indoor / Outdoor")
with s2:
    metric_card("Fan", "ON" if data.get("fan_on") else "OFF", "Ventilation output")
with s3:
    metric_card("Air status", str(data.get("air_status") or "—"), "Based on configured threshold")
with s4:
    metric_card("Temperature status", str(data.get("temperature_status") or "—"), "Based on configured threshold")

st.markdown("### OUTPUT INDICATORS")
o1, o2, o3, o4 = st.columns(4)
with o1:
    metric_card("Relay", "ON" if data.get("relay_on") else "OFF")
with o2:
    metric_card("Red LED", "ON" if data.get("red_led") else "OFF")
with o3:
    metric_card("Green LED", "ON" if data.get("green_led") else "OFF")
with o4:
    metric_card("Buzzer", "ON" if data.get("buzzer_on") else "OFF")

alert = data.get("alert_message") or "No active alert reported."
if alert.lower() not in ("", "none", "no alert", "normal"):
    st.warning("⚠️ " + alert)
else:
    st.success("✓ " + alert)

timestamp = data.get("timestamp")
if timestamp:
    st.caption(f"Latest reading timestamp (UTC): {timestamp}")

# ---------- Analytics ----------
st.markdown("---")
st.markdown("### SENSOR ANALYTICS")
if history:
    df = pd.DataFrame(history)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp")
    chart1, chart2 = st.columns(2)
    with chart1:
        if "mq135" in df.columns:
            fig = px.line(df, x="timestamp" if "timestamp" in df else df.index,
                          y="mq135", title="Air quality sensor trend")
            fig.update_layout(template="plotly_dark", paper_bgcolor="#0b1220",
                              plot_bgcolor="#121f30", margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig, use_container_width=True)
    with chart2:
        cols = [c for c in ["temperature", "humidity"] if c in df.columns]
        if cols:
            fig = px.line(df, x="timestamp" if "timestamp" in df else df.index,
                          y=cols, title="Temperature and humidity trend")
            fig.update_layout(template="plotly_dark", paper_bgcolor="#0b1220",
                              plot_bgcolor="#121f30", margin=dict(l=10,r=10,t=45,b=10))
            st.plotly_chart(fig, use_container_width=True)
    with st.expander("View received telemetry records"):
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.info("No history records available yet.")

st.caption("Note: MQ135 readings shown here are raw ADC values, not calibrated gas concentration or a certified air-quality measurement.")
