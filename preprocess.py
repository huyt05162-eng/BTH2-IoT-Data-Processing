import pandas as pd
import numpy as np
import json
import paho.mqtt.publish as publish
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sklearn.preprocessing import MinMaxScaler
import warnings

warnings.filterwarnings('ignore')

# === CẤU HÌNH THINGSBOARD ===
TB_HOST = "eu.thingsboard.cloud"
TB_TOKEN = "oMCILc15Ff2OGOq16FZy"
TB_TOPIC = "v1/devices/me/telemetry"

# === CẤU HÌNH INFLUXDB ===
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "KsQskEH6ww_Pc-SIRA4h8IZ9ad3KViZDNtFATJcpcKn7ySkCw5pNX9y4LDfjGXIxwtpV8oQ0aTc3m8LqPBi-TQ=="
INFLUXDB_ORG = "PTIT"
SOURCE_BUCKET = "iot_raw"
DEST_BUCKET = "iot_processed"

client_db = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG, timeout=30000)
query_api = client_db.query_api()
write_api = client_db.write_api(write_options=SYNCHRONOUS)

def preprocess_data():
    print("1. Đang truy vấn dữ liệu thô...")
    query = f'''
        from(bucket: "{SOURCE_BUCKET}")
        |> range(start: -10m)
        |> filter(fn: (r) => r["_measurement"] == "sensor_data")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    df = query_api.query_data_frame(query)

    if df.empty:
        print("Không có dữ liệu mới.")
        return

    df['_time'] = pd.to_datetime(df['_time'])
    df.set_index('_time', inplace=True)
    cols_to_process = ['temperature', 'humidity', 'distance_cm']
    df = df[cols_to_process]

    print("2. Xử lý thiếu hụt & nhiễu...")
    df = df.interpolate(method='time').bfill().ffill()
    for col in cols_to_process:
        z_scores = np.abs((df[col] - df[col].mean()) / (df[col].std() + 1e-9))
        df.loc[z_scores > 3, col] = np.nan
    df = df.interpolate(method='time').bfill().ffill()

    print("3. Resampling & Chuẩn hóa...")
    df_resampled = df.resample('10s').mean().dropna()
    scaler = MinMaxScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_resampled), 
                             columns=[f"{col}_scaled" for col in cols_to_process], 
                             index=df_resampled.index)
    df_final = pd.concat([df_resampled, df_scaled], axis=1)

    print("4. Ghi InfluxDB & Đẩy lên ThingsBoard...")
    points = []
    for index, row in df_final.iterrows():
        p = Point("sensor_data_cleaned").tag("student_id", "B23DCAT136").time(index)
        for col in df_final.columns:
            p.field(col, float(row[col]))
        points.append(p)
    write_api.write(bucket=DEST_BUCKET, org=INFLUXDB_ORG, record=points)
    
    # Lấy dòng mới nhất để đẩy lên ThingsBoard
    latest_row = df_final.iloc[-1]
    tb_clean_payload = json.dumps({
        "temperature_clean": float(latest_row['temperature']),
        "humidity_clean": float(latest_row['humidity']),
        "distance_clean": float(latest_row['distance_cm']),
        "temp_scaled": float(latest_row['temperature_scaled'])
    })
    
    try:
        publish.single(TB_TOPIC, payload=tb_clean_payload, hostname=TB_HOST, port=1883, auth={'username': TB_TOKEN})
        print(f"-> Hoàn tất! Đã ghi {len(points)} bản ghi vào DB và update ThingsBoard.")
    except Exception as e:
        print(f"-> Ghi DB thành công nhưng lỗi đẩy ThingsBoard: {e}")

if __name__ == "__main__":
    preprocess_data()