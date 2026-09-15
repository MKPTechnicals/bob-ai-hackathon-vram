from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import pandas as pd
import os
from typing import List

from src.data import generate_synthetic_data
from src.model import ForecastModel, AnomalyDetector
from src.optimizer import recommend_actions
from src.bob_integration import generate_operator_brief

# simple API key header for frontend auth
API_KEY_NAME = 'x-api-key'
API_KEY = os.environ.get('FRONTEND_API_KEY', '')
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

clients: List[WebSocket] = []


async def get_api_key(header: str = Depends(api_key_header)):
    if not API_KEY:
        return True
    if header == API_KEY:
        return True
    raise HTTPException(status_code=401, detail='Invalid or missing API Key')

app = FastAPI(title="Bobathon Grid Optimiser")

# Serve static frontend
app.mount('/static', StaticFiles(directory='src/static'), name='static')


@app.get("/")
def root():
    return FileResponse('src/static/index.html')

class ForecastRequest(BaseModel):
    hours: int = 24

class RecommendRequest(BaseModel):
    forecast: dict
    anomalies: dict


# Initialize in-memory components (demo mode)
_df = generate_synthetic_data(days=14)
# Try to load persisted model if available
MODEL_PATH = os.path.join('src', 'models', 'reservoir.npz')
forecast_model = None
if os.path.exists(MODEL_PATH):
    try:
        forecast_model = ForecastModel.load(MODEL_PATH)
    except Exception:
        forecast_model = None
if forecast_model is None:
    forecast_model = ForecastModel()
    forecast_model.train(_df)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    try:
        forecast_model.save(MODEL_PATH)
    except Exception:
        pass

anomaly_detector = AnomalyDetector()
anomaly_detector.train(_df)


async def broadcast_event(event_type: str, payload: dict):
    body = {'type': event_type, 'payload': payload}
    remove = []
    for ws in clients:
        try:
            await ws.send_json(body)
        except Exception:
            remove.append(ws)
    for r in remove:
        try:
            clients.remove(r)
        except Exception:
            pass


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/forecast")
def forecast(req: ForecastRequest, authorized: bool = Depends(get_api_key)):
    try:
        preds = forecast_model.predict_hours(req.hours)
        # push to connected clients
        try:
            import asyncio
            asyncio.create_task(broadcast_event('forecast', {'hours': req.hours, 'forecast': preds}))
        except Exception:
            pass
        return {"hours": req.hours, "forecast": preds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies")
def anomalies(authorized: bool = Depends(get_api_key)):
    res = anomaly_detector.detect_recent(_df)
    try:
        import asyncio
        asyncio.create_task(broadcast_event('anomalies', res))
    except Exception:
        pass
    return res


@app.post("/recommend")
def recommend(req: RecommendRequest, authorized: bool = Depends(get_api_key)):
    try:
        actions = recommend_actions(req.forecast, req.anomalies)
        brief = generate_operator_brief(req.forecast, req.anomalies, actions, use_bob=True)
        try:
            import asyncio
            asyncio.create_task(broadcast_event('recommend', {'actions': actions, 'brief': brief}))
        except Exception:
            pass
        return {"actions": actions, "brief": brief}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket('/ws')
async def websocket_endpoint(ws: WebSocket):
    # Accept optional token query param for auth
    token = ws.query_params.get('token')
    if API_KEY and token != API_KEY:
        await ws.close(code=1008)
        return
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        try:
            clients.remove(ws)
        except Exception:
            pass
