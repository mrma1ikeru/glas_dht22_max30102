import serial
import json

ser = serial.Serial('/dev/cu.usbserial-1140', 115200, timeout=1)

while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()

    if not line:
        continue

    try:
        data = json.loads(line)

        sensor = data.get("sensor")

        if sensor == "DHT22":
            print("=== DHT22 ===")
            print("Температура:", data.get("temperature_c"), "°C")
            print("Влажность:", data.get("humidity_rh"), "%")
            print("Статус:", data.get("sensor_status"))

        elif sensor == "MAX30102":
            print("=== MAX30102 ===")
            print("Пульс:", data.get("hr_bpm"), "уд/мин")
            print("SpO2:", data.get("spo2_percent"), "%")
            print("Качество сигнала:", data.get("signal_quality"))
            print("Статус:", data.get("sensor_status"))

        else:
            print("Неизвестный датчик:", sensor)

        print("-" * 40)

    except json.JSONDecodeError:
        print("Некорректный JSON:", line)