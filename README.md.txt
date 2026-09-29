# Bài thực hành 2: Thu thập và Tiền xử lý dữ liệu IoT

## 1. Thông tin sinh viên
- **Họ và tên:** Trần Ngọc Huy
- **Mã sinh viên:** B23DCAT136

## 2. Kiến trúc hệ thống
- **Edge Device:** ESP32 giả lập trên Wokwi, gửi dữ liệu qua MQTT (HiveMQ).
- **Gateway & Storage:** Python Script nhận dữ liệu từ MQTT lưu vào InfluxDB (Local).
- **Preprocessing:** Sử dụng Pandas xử lý ngoại lai (Z-score), điền khuyết và chuẩn hóa (MinMaxScaler).
- **Application/Dashboard:** ThingsBoard Cloud hiển thị dữ liệu thời gian thực.

## 3. Hướng dẫn cài đặt
1. Cài đặt Python 3 và InfluxDB 2.x (chạy qua Docker).
2. Cài đặt thư viện: `pip install -r requirements.txt`
3. Mở mã nguồn phần cứng trên Wokwi và nhấn Start Simulation.

## 4. Hướng dẫn chạy hệ thống
- **Terminal 1:** Chạy `python subscriber.py` để thu thập dữ liệu thô đẩy vào InfluxDB và ThingsBoard.
- **Terminal 2:** Chạy `python preprocess.py` để làm sạch dữ liệu, lọc nhiễu và đẩy kết quả chuẩn hóa lên ThingsBoard.