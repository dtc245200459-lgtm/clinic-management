# Bước 6.3 — Giám sát Django/Nginx bằng Prometheus và Grafana

Áp dụng cho dự án đã chạy thành công https://localhost:8443/ ở Bước 6.2.

Gói này bổ sung **3 dịch vụ**: `blackbox`, `prometheus`, `grafana`, và một dashboard theo dõi Django/Nginx. Không thay `compose.yaml`, `compose.override.yaml`, `compose.https.yaml`, Django code, cơ sở dữ liệu hay chứng chỉ HTTPS.

## 0. Rất quan trọng

- Chỉ dùng **dữ liệu giả lập** cho dự án học tập.
- Không chạy `docker compose down -v`: tham số `-v` có thể xóa volume dữ liệu PostgreSQL.
- Không chụp/gửi nội dung `.env`, mật khẩu, khóa SSL `localhost.key`.
- Chỉ mở cổng giám sát trên máy bạn: `127.0.0.1`. Đây chưa phải cấu hình dùng cho Internet.
- Chặng đầu này kiểm tra **HTTP health check**, chưa đo CPU/RAM, lượng yêu cầu thực tế hoặc thống kê bệnh nhân. Loki/Promtail sẽ là chặng riêng sau.

## 1. Mở đúng thư mục VS Code

Trong VS Code chọn Terminal -> New Terminal (PowerShell). Thư mục đang đứng phải chứa các file Bước 6.2.

```powershell
Test-Path .\compose.yaml
Test-Path .\compose.override.yaml
Test-Path .\compose.https.yaml
```

Cả ba cần `True`. Nếu có `False`, dừng và mở lại đúng thư mục dự án (thường là thư mục lồng bên trong Downloads).

## 2. Kiểm tra rồi giải nén ZIP

Chạy:

```powershell
Test-Path .\compose.monitoring.yaml
Test-Path .\monitoring\prometheus.yml
Test-Path .\monitoring\grafana\dashboards\clinic-overview.json
```

**Chỉ giải nén nếu cả ba đều `False`.** Nếu đã có file, đừng dùng `Expand-Archive -Force`: hãy gửi ảnh để kiểm tra trước.

Tải `clinic-management-step6-3-update.zip` vào Downloads, rồi chạy:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step6-3-update.zip" -DestinationPath .
```

Xác minh:

```powershell
Test-Path .\compose.monitoring.yaml
Test-Path .\monitoring\prometheus.yml
Test-Path .\monitoring\grafana\dashboards\clinic-overview.json
```

Cả ba cần `True`.

## 3. Đặt mật khẩu Grafana trong .env

Trong Explorer của VS Code, mở file `.env` sẵn có nằm cùng cấp với `compose.yaml`.

Thêm **một dòng mới** ở cuối file (thay phần sau dấu `=` bằng mật khẩu mạnh riêng của bạn, ít nhất 16 ký tự, dùng chữ và số để đơn giản):

```dotenv
GRAFANA_ADMIN_PASSWORD=DAT_MAT_KHAU_MOI_RIENG_CUA_BAN
```

**KHÔNG dùng chính chuỗi ví dụ này làm mật khẩu.** Không xóa các dòng `POSTGRES_...` hay `DJANGO_...`. Nhấn `Ctrl + S` để lưu. Nếu `.env` đã có `GRAFANA_ADMIN_PASSWORD`, không thêm dòng trùng, báo mình nếu không rõ.

Kiểm tra sự tồn tại mà **không in mật khẩu**:

```powershell
Select-String -Path .\.env -Pattern '^GRAFANA_ADMIN_PASSWORD=' -Quiet
```

Cần ra `True`. Đừng chụp nội dung file `.env`.

## 4. Kiểm tra Docker Compose

Từ bước này, luôn dùng **4 file `-f`** để kế thừa HTTPS và giữ cấu hình hiện có:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml config -q
```

Không có thông báo lỗi nghĩa là cấu hình hợp lệ. Nếu có lỗi, dừng và gửi ảnh **chỉ dòng lỗi, không in toàn bộ config có mật khẩu**.

Liệt kê các dịch vụ:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml config --services
```

Kết quả phải có `db`, `web`, `nginx`, `blackbox`, `prometheus`, `grafana` (thứ tự tùy ý).

## 5. Khởi động riêng 3 dịch vụ giám sát

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml up -d blackbox prometheus grafana
```

Lần đầu Docker cần tải các image, có thể mất vài phút. Lệnh chỉ tạo/khởi động dịch vụ giám sát và không yêu cầu xóa database.

Kiểm tra:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml ps -a
```

Đợi vài chục giây cho Prometheus thu thập dữ liệu.

## 6. Kiểm tra Prometheus

Mở trình duyệt: **http://localhost:9091/**

Trong Prometheus, chọn mục **Status -> Target health** hoặc **Status -> Targets** (tên menu tùy phiên bản). Cần thấy `prometheus` và `clinic_http`.

Vào trang Query, nhập:

```promql
probe_success{job="clinic_http"}
```

Sau 15–30 giây, mong đợi có hai chuỗi số liệu bằng `1`:

- `http://web:8000/health/` = 1 (Django hoạt động)
- `http://nginx:80/health/` = 1 (Nginx HTTP hoạt động)

Đây là **tên nội bộ Docker**, không phải địa chỉ cần mở trên Windows.

## 7. Kiểm tra Grafana

Mở: **http://localhost:3001/**

- Tên đăng nhập: `admin`
- Mật khẩu: mật khẩu `GRAFANA_ADMIN_PASSWORD` bạn đã tự đặt trong `.env`.
- Vào **Dashboards -> Clinic Monitoring -> Phòng khám — Giám sát hoạt động**.

Sẽ thấy: trạng thái Django/Nginx, trạng thái Prometheus, thời gian kiểm tra và mã HTTP. Chờ 30–60 giây để biểu đồ có dữ liệu.

## 8. Nếu lỗi

Kiểm tra an toàn:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml ps -a
```

Xem log *dịch vụ giám sát*, không cần in thông tin bí mật:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml logs --tail=60 blackbox prometheus grafana
```

- `port is already allocated` tại 9091 hoặc 3001: dừng, báo mình, không xóa container khác.
- `GRAFANA_ADMIN_PASSWORD` missing: kiểm tra `.env`, không gửi mật khẩu cho mình.
- `targets` bị `DOWN`, `probe_success=0`: gửi ảnh Prometheus Targets và `docker compose ... ps -a`.
- Grafana không đăng nhập: xác minh đã dùng mật khẩu tự đặt; lưu ý thay `.env` **sau khi Grafana đã khởi tạo database lần đầu** không tự đổi mật khẩu hiện có.
- Dashboard chưa hiện: gửi ảnh mục **Dashboards** và log Grafana.

## 9. Ý nghĩa từng thành phần

| Thành phần | Cổng trên Windows | Vai trò |
|---|---|---|
| Django + Nginx | 8081 / 8443 | Ứng dụng phòng khám hiện tại |
| Blackbox | Không mở cổng ra Windows | Kiểm tra địa chỉ /health/ từ mạng Docker |
| Prometheus | http://localhost:9091 | Thu thập và lưu số liệu ngắn hạn (3 ngày) |
| Grafana | http://localhost:3001 | Hiển thị biểu đồ đã cấu hình sẵn |

Phạm vi hiện tại: giám sát **tính sẵn sàng HTTP**. Nếu hoàn tất ổn, chúng ta có thể làm tiếp Loki/Promtail cho log đã lọc dữ liệu nhạy cảm, rồi cân nhắc metrics tài nguyên và CSDL.
