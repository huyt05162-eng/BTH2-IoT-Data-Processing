import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from paho.mqtt.enums import CallbackAPIVersion
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# === CẤU HÌNH MQTT (WOKWI -> HINEMQ) ===
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "ptit/b23dcat136/sensors"

# === CẤU HÌNH THINGSBOARD ===
TB_HOST = "eu.thingsboard.cloud"
TB_TOKEN = "oMCILc15Ff2OGOq16FZy"
TB_TOPIC = "v1/devices/me/telemetry"

# === CẤU HÌNH INFLUXDB ===
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "KsQskEH6ww_Pc-SIRA4h8IZ9ad3KViZDNtFATJcpcKn7ySkCw5pNX9y4LDfjGXIxwtpV8oQ0aTc3m8LqPBi-TQ=="
INFLUXDB_ORG = "PTIT"
INFLUXDB_BUCKET = "iot_raw"

client_db = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Đã kết nối MQTT Broker. Đang lắng nghe: {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        # Giải mã dữ liệu
        data = json.loads(msg.payload.decode('utf-8'))
        print(f"\n[NHẬN] Dữ liệu thô: {data}")

        # 1. Ghi vào InfluxDB
        point = (
            Point("sensor_data")
            .tag("student_id", "B23DCAT136")
            .field("temperature", float(data["temperature"]))
            .field("humidity", float(data["humidity"]))
            .field("distance_cm", float(data["distance_cm"]))
            .field("rssi", int(data["rssi"]))
            .field("sequence", int(data["sequence"]))
            .field("uptime_s", int(data["uptime_s"]))
        )
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        
        # 2. Forward sang ThingsBoard
        tb_payload = json.dumps({
            "temperature_raw": float(data["temperature"]),
            "humidity_raw": float(data["humidity"]),
            "distance_raw": float(data["distance_cm"])
        })
        publish.single(TB_TOPIC, payload=tb_payload, hostname=TB_HOST, port=1883, auth={'username': TB_TOKEN})
        print("[GỬI] Đã lưu InfluxDB và đẩy lên ThingsBoard thành công!")

    except Exception as e:
        print(f"Lỗi: {e}")

mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Khởi động Subscriber...")
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_forever()