from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Measurement(BaseModel):
    timestamp: datetime

    temp_air: Optional[float]
    humidity: Optional[float]

    heart_rate: Optional[int]
    spo2: Optional[int]


class TelemetryBatch(BaseModel):
    device_id: str
    measurements: List[Measurement]