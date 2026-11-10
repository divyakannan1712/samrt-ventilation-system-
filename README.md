# Smart Ventilation — Complete Software

This project contains both the Streamlit dashboard and FastAPI backend.

## Files
- `app.py` — Streamlit website/dashboard
- `backend.py` — FastAPI server receiving ESP32 telemetry
- `requirements.txt` — dependencies

## 1. Run locally (computer)
Install dependencies:
```bash
python -m pip install -r requirements.txt
```

Terminal 1 — backend:
```bash
python -m uvicorn backend:app --host 0.0.0.0 --port 8000
```

Terminal 2 — dashboard:
```bash
streamlit run app.py
```

In the dashboard sidebar, set API address to:
`http://127.0.0.1:8000`

## 2. Deploy backend on Render
Push `backend.py` and `requirements.txt` to a GitHub repository, then create a Render Web Service:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend:app --host 0.0.0.0 --port $PORT`

After deployment, copy the Render URL, e.g. `https://your-backend.onrender.com`.

## 3. Connect hosted Streamlit dashboard
In the website sidebar, change API address to the Render URL (without `/api/...`):
`https://your-backend.onrender.com`

## 4. Connect ESP32
In the ESP32 sketch, set:
```cpp
const char* API_URL = "https://your-backend.onrender.com/api/telemetry";
```
Keep the JSON field names consistent with the `Telemetry` model in `backend.py`.

## Important deployment note
SQLite on a free web host may be stored on temporary local disk and can be lost when the service restarts/redeploys. Use a persistent disk or managed database if you need durable history. Keep Wi-Fi credentials out of public GitHub repositories. This starter API does not authenticate incoming telemetry; use it for a controlled prototype and add authentication before public production use.

## Data note
MQ135 is shown as its raw ADC value. It is not a calibrated ppm or certified air-quality reading.
