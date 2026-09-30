import serial
import json
import requests
from datetime import datetime


SERIAL_PORT = "/dev/cu.usbserial-1140"
BAUD_RATE = 115200

API_URL = "http://127.0.0.1:8000/api/v1/telemetry"


ser = serial.Serial(
    SERIAL_PORT,
    BAUD_RATE,
    timeout=1
)

print("Подключено к Arduino:", SERIAL_PORT)
print("Ожидание данных...")
print("-" * 50)


latest_data = {
    "device_id": None,
    "temperature_c": None,
    "humidity_rh": None,
    "heart_rate": None,
    "spo2": None
}


while True:

    line = ser.readline().decode(
        "utf-8",
        errors="ignore"
    ).strip()

    if not line:
        continue

    try:
        data = json.loads(line)

    except json.JSONDecodeError:
        print("Некорректный JSON:")
        print(line)
        continue

    sensor = data.get("sensor")

    if sensor == "DHT22":

        latest_data["device_id"] = data.get("device_id")

        latest_data["temperature_c"] = data.get(
            "temperature_c"
        )

        latest_data["humidity_rh"] = data.get(
            "humidity_rh"
        )

        print("Получен DHT22")
        print(
            "Температура:",
            latest_data["temperature_c"],
            "°C"
        )
        print(
            "Влажность:",
            latest_data["humidity_rh"],
            "%"
        )

    elif sensor == "MAX30102":

        latest_data["device_id"] = data.get("device_id")

        latest_data["heart_rate"] = data.get(
            "hr_bpm"
        )

        latest_data["spo2"] = data.get(
            "spo2_percent"
        )

        print("Получен MAX30102")
        print(
            "Пульс:",
            latest_data["heart_rate"],
            "уд/мин"
        )
        print(
            "SpO2:",
            latest_data["spo2"],
            "%"
        )
        print(
            "Качество сигнала:",
            data.get("signal_quality")
        )

    else:
        print("Неизвестный датчик:", sensor)
        continue

    print("-" * 50)

    # Проверяем, есть ли данные обоих датчиков

    if (
        latest_data["device_id"] is not None
        and latest_data["temperature_c"] is not None
        and latest_data["humidity_rh"] is not None
        and latest_data["heart_rate"] is not None
        and latest_data["spo2"] is not None
    ):

        telemetry = {
            "device_id": latest_data["device_id"],

            "measurements": [
                {
                    "timestamp": datetime.now().isoformat(),

                    "temp_air": latest_data["temperature_c"],

                    "humidity": latest_data["humidity_rh"],

                    "heart_rate": latest_data["heart_rate"],

                    "spo2": latest_data["spo2"]
                }
            ]
        }

        try:

            response = requests.post(
                API_URL,
                json=telemetry,
                timeout=5
            )

            print("Отправлено в GLAS backend")

            print("HTTP статус:", response.status_code)

            print("Ответ сервера:", response.text)

        except requests.RequestException as error:

            print("Ошибка подключения к FastAPI:")
            print(error)

        print("=" * 50)