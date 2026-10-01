import json
import time
from datetime import datetime, timezone

import requests
import serial

PORT = "/dev/cu.usbserial-1140"
BAUD = 115200
API_URL = "http://127.0.0.1:8000/api/v1/telemetry"
DEVICE_ID = "node_01"
SEND_EVERY = 2          # секунд между отправками

ser = serial.Serial(PORT, BAUD, timeout=1)
buffer = []             # накопленные измерения
last_send = time.time()


def to_measurement(data):
    """Превращает JSON от Arduino в измерение для бэкенда."""
    m = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temp_air": None,
        "humidity": None,
        "heart_rate": None,
        "spo2": None,
    }
    sensor = data.get("sensor")
    if sensor == "DHT22":
        m["temp_air"] = data.get("temperature_c")
        m["humidity"] = data.get("humidity_rh")
    elif sensor == "MAX30102":
        m["heart_rate"] = data.get("hr_bpm")
        m["spo2"] = data.get("spo2_percent")
    else:
        return None
    return m


def flush():
    """Отправляет накопленные измерения. При ошибке оставляет их в буфере."""
    global buffer
    if not buffer:
        return
    try:
        r = requests.post(
            API_URL,
            json={"device_id": DEVICE_ID, "measurements": buffer},
            timeout=5,
        )
        if r.ok:
            print(f"-> отправлено {len(buffer)}: {r.json()}")
            buffer = []
        else:
            print("Сервер ответил", r.status_code, r.text)
    except requests.RequestException as e:
        print("Нет связи с сервером, повторю позже:", e)


while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()

    if line:
        try:
            data = json.loads(line)
            print(data)
            m = to_measurement(data)
            if m:
                buffer.append(m)
        except json.JSONDecodeError:
            print("Некорректный JSON:", line)

    if time.time() - last_send >= SEND_EVERY:
        flush()
        last_send = time.time()