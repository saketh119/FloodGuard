from fastapi import APIRouter

from app.api.v1 import events, stations, weather, predictions, chat, rivers

router = APIRouter()

router.include_router(events.router, prefix="/events", tags=["Events"])
router.include_router(stations.router, prefix="/stations", tags=["Stations"])
router.include_router(weather.router, prefix="/weather", tags=["Weather"])
router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(rivers.router, prefix="/rivers", tags=["Rivers"])
