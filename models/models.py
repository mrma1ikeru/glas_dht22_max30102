from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from db.database import Base
from datetime import datetime


class RawMeasurement(Base):             #прост показатели
    __tablename__ = "raw_measurements"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)

    temp_air = Column(Float)
    humidity = Column(Float)

    heart_rate = Column(Integer)
    spo2 = Column(Integer)


class DeviceStatus(Base):           #статус девайса
    __tablename__ = "device_status"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    last_seen = Column(DateTime)
    status = Column(String)
    last_payload_ok = Column(Boolean)
    queue_size = Column(Integer)
    updated_at = Column(DateTime, default=datetime.now)


class Alert(Base):          #причина тревоги если капец
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    device_id = Column(String)
    timestamp = Column(DateTime, index=True)
    alert_type = Column(String)
    message = Column(String)