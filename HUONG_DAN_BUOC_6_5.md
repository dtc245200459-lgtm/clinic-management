# Bước 6.5 — Kiểm tra CPU/RAM và đưa PostgreSQL vào Grafana

## Phạm vi

Phần 6.5 này gồm hai việc: **(A)** xem CPU/RAM từng container trực tiếp bằng lệnh Docker an toàn; **(B)** thêm PostgreSQL Exporter để Prometheus thu thập số liệu và Grafana hiển thị dashboard mới. Không thay đổi dữ liệu, schema, migration hay thông tin bệnh nhân.

**Chưa tự động hóa CPU/RAM lên Grafana**: nhiều cách làm yêu cầu gắn Docker socket hoặc filesystem máy chủ vào container giám sát. Chúng ta để riêng phần đó để xem xét quyền truy cập sau, không bật mặc định.

## A. Xem CPU/RAM ngay trong VS Code Windows

Mở Docker Desktop, sau đó mở VS Code -> Terminal -> New Terminal (PowerShell). Chạy:

```powershell
docker stats --no-stream
```

Các cột có `CPU %`, `MEM USAGE / LIMIT`, `MEM %`, `NET I/O`. Đây là **ảnh chụp số liệu tại thời điểm chạy**, không phải biểu đồ lịch sử.

Nếu muốn tự cập nhật liên tục, dùng `docker stats` và bấm `Ctrl + C` để thoát; lệnh không xóa dữ liệu.

## B1. Kiểm tra file dự án trước khi giải nén

Bạn phải đứng trong thư mục cùng cấp với 5 file Compose đã chạy tới Bước 6.4.

```powershell
Test-Path .\compose.yaml
Test-Path .\compose.override.yaml
Test-Path .\compose.https.yaml
Test-Path .\compose.monitoring.yaml
Test-Path .\compose.logs.yaml
```

Cả 5 cần `True`.

Các file mới phải **chưa tồn tại**:

```powershell
Test-Path .\compose.metrics.yaml
Test-Path .\monitoring\prometheus-metrics.yml
Test-Path .\monitoring\grafana\dashboards\postgres-overview.json
```

Chỉ giải nén nếu cả 3 là `False`. Nếu có `True`, dừng lại; **không dùng `Expand-Archive -Force`**.

Tải `clinic-management-step6-5-update.zip` vào Downloads, rồi chạy:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step6-5-update.zip" -DestinationPath .
```

Kiểm tra lại 3 file mới bằng `Test-Path`, tất cả cần `True`.

## B2. Kiểm tra Compose (6 file)

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml -f compose.metrics.yaml config -q
```

Nếu không có lỗi, chạy tiếp:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml -f compose.metrics.yaml config --services
```

Cần có 9 dịch vụ: `db`, `web`, `nginx`, `blackbox`, `prometheus`, `grafana`, `loki`, `alloy`, `postgres_exporter`.

**Không chạy `docker compose config` không có `-q` rồi chụp ảnh**, vì cấu hình đầy đủ có thể in mật khẩu cơ sở dữ liệu được truyền sang exporter.

## B3. Khởi động PostgreSQL Exporter và cập nhật Prometheus

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml -f compose.metrics.yaml up -d postgres_exporter prometheus
```

Docker có thể tải một image mới và tạo lại container Prometheus do thay đổi cấu hình thu thập dữ liệu. **Volume dữ liệu Prometheus và PostgreSQL được giữ nguyên.**

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml -f compose.metrics.yaml ps -a
```

Mong đợi 9 dịch vụ đều `Up` và `db` ở trạng thái `healthy`.

## B4. Kiểm tra Prometheus

Mở **http://localhost:9091/**, vào phần Query/Explore và nhập:

```promql
pg_up{job="postgres"}
```

Bấm Execute/Run query, chờ 15–30 giây. Nếu kết quả bằng **1**, PostgreSQL Exporter đã kết nối được PostgreSQL.

Có thể kiểm tra thêm số kết nối đang mở:

```promql
pg_stat_database_numbackends{job="postgres"}
```

Các số liệu này là thống kê hệ thống, không phải dữ liệu bệnh nhân.

## B5. Kiểm tra Grafana

Mở **http://localhost:3001/** và đăng nhập bằng tài khoản Grafana cũ.

Vào **Dashboards -> Clinic Monitoring -> Phòng khám — Giám sát PostgreSQL**.

Bạn sẽ thấy các bảng: trạng thái DB, số kết nối, dung lượng database và tốc độ giao dịch. Biểu đồ giao dịch cần ít nhất vài phút để bắt đầu có điểm dữ liệu.

Grafana tự quét lại các file dashboard (khoảng 30 giây). Nếu chưa thấy dashboard sau một phút, chạy lệnh an toàn sau để khởi động lại riêng Grafana:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml -f compose.metrics.yaml restart grafana
```

## Lưu ý bảo mật rất quan trọng

- Gói này sử dụng **thông tin đăng nhập PostgreSQL hiện có từ `.env`** để exporter đọc các thống kê kỹ thuật. Đó là giải pháp đơn giản cho **đồ án local có dữ liệu giả**; chưa phải mô hình phân quyền tối thiểu cho bệnh viện thực tế.
- Exporter **không mở cổng ra Windows/Internet**. Chỉ Prometheus trong mạng Docker đọc các số liệu từ nó.
- Khi làm Bước 7, chúng ta nên tạo tài khoản giám sát riêng chỉ có quyền phù hợp (`pg_monitor`), thay vì dùng tài khoản database của ứng dụng.
- **Không gửi ảnh `.env`**, khóa SSL hoặc cấu hình đã bung biến môi trường có mật khẩu.
- Không dùng `docker compose down -v`: lệnh có thể xóa dữ liệu trong volume PostgreSQL.
- Nếu xảy ra lỗi, gửi ảnh `ps -a` và log exporter/Prometheus, **không gửi mật khẩu**.
