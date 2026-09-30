from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import asyncio

from db.database import SessionLocal
from models.models import RawMeasurement, Alert, DeviceStatus
from schemas.telemetry import TelemetryBatch

import os
from dotenv import load_dotenv
load_dotenv()

NO_DATA_TIMEOUT = int(os.getenv("NO_DATA_TIMEOUT", 60))             #конфигурация окружения
BACKLOG_THRESHOLD = int(os.getenv("BACKLOG_THRESHOLD", 20))

@asynccontextmanager                #lifespan вместо startup; написано, что эт современная вресия
async def lifespan(app: FastAPI):

    asyncio.create_task(check_no_data())

    yield

app = FastAPI(lifespan=lifespan)            #инициализация апи
@app.get("/")
def root():
    return {"status": "GLAS backend running"}
telemetry_router = APIRouter()
app.include_router(telemetry_router)

def get_db():           #зависимость бд
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.exception_handler(RequestValidationError)          #если ошибки
async def validation_exception_handler(exc: RequestValidationError):

    return JSONResponse(
        status_code=422,
        content={
            "error": "bad_payload",
            "details": exc.errors()
        }
    )

@app.get("/api/v1/devices")
def get_devices(db: Session = Depends(get_db)):         #апи девайсов

    devices = db.query(DeviceStatus).all()

    return devices

@app.get("/api/v1/alerts")
def get_alerts(db: Session = Depends(get_db)):          #если капецц с девайсом/значением

    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(100).all()

    return alerts

async def check_no_data():

    while True:

        db = SessionLocal()

        devices = db.query(DeviceStatus).all()

        for device in devices:

            if device.last_seen:

                diff = datetime.utcnow() - device.last_seen

                if diff > timedelta(seconds=NO_DATA_TIMEOUT):

                    alert = Alert(
                        device_id=device.device_id,
                        timestamp=datetime.utcnow(),
                        alert_type="no_data",
                        message="Device stopped sending data"
                    )

                    db.add(alert)

        db.commit()
        db.close()

        await asyncio.sleep(30)
@app.post("/api/v1/telemetry")          #девайсы: апи, тревоги и тп
def receive_telemetry(batch: TelemetryBatch, db: Session = Depends(get_db)):
    device = db.query(DeviceStatus).filter(
        DeviceStatus.device_id == batch.device_id
    ).first()
    if not device:
        device = DeviceStatus(device_id=batch.device_id)
        db.add(device)

    device.last_seen = datetime.utcnow()
    device.status = "online"
    device.last_payload_ok = True

    batch_size = len(batch.measurements)

    if batch_size > BACKLOG_THRESHOLD:
        alert = Alert(
            device_id=batch.device_id,
            timestamp=datetime.utcnow(),
            alert_type="queue_backlog",
            message=f"Large telemetry batch received: {batch_size}"
        )

        db.add(alert)

    accepted = 0

    for m in batch.measurements:

        measurement = RawMeasurement(
            device_id=batch.device_id,
            timestamp=m.timestamp,
            temp_air=m.temp_air,
            humidity=m.humidity,
            heart_rate=m.heart_rate,
            spo2=m.spo2,
        )
        db.add(measurement)

        if m.temp_air is not None and m.temp_air > 30:
            alert = Alert(
                device_id=batch.device_id,
                timestamp=m.timestamp,
                alert_type="high_temp_air",
                message="Air temperature too high"
            )
            db.add(alert)

        if m.humidity is not None and m.humidity < 30:
            alert = Alert(
                device_id=batch.device_id,
                timestamp=m.timestamp,
                alert_type="low_humidity",
                message="Humidity too low"
            )
            db.add(alert)

        accepted += 1

    db.commit()

    return {"accepted": accepted}

@app.get("/api/v1/measurements")
def get_measurements(db: Session = Depends(get_db)):
    measurements = (
        db.query(RawMeasurement)
        .order_by(RawMeasurement.timestamp.desc())
        .limit(10)
        .all()
    )

    return measurements