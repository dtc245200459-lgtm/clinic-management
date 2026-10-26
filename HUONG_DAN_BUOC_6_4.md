# Bước 6.4 — Nhật ký an toàn với Loki + Grafana Alloy

## Mục tiêu và phạm vi

Sau Bước 6.3, bạn đã có Django + PostgreSQL + Nginx HTTPS + Prometheus + Grafana hoạt động. Bước 6.4 thêm **Loki** để lưu nhật ký và **Grafana Alloy** để đọc nhật ký từ file Nginx.

**Tại sao không dùng Promtail?** Promtail đã hết vòng đời hỗ trợ từ 02/03/2026; Grafana khuyến nghị dùng Alloy.

**Quyền riêng tư:** Gói này chỉ thu thập log HTTP tối giản gồm *thời gian, GET/POST, mã HTTP, số giây xử lý*. Không thu thập địa chỉ IP, URL, câu tìm kiếm, cookie, nội dung biểu mẫu hay dữ liệu bệnh án. Đây là log trạng thái Nginx phản ánh phản hồi của ứng dụng, **chưa phải toàn bộ lỗi nội bộ Django**. Không cấp Docker socket cho Alloy.

## 1. Kiểm tra thư mục Windows trước khi giải nén

Trong VS Code mở Terminal -> New Terminal (PowerShell). Phải ở thư mục có 4 file hiện tại:

```powershell
Test-Path .\compose.yaml
Test-Path .\compose.override.yaml
Test-Path .\compose.https.yaml
Test-Path .\compose.monitoring.yaml
```

Cả bốn cần `True`.

Kiểm tra file mới **trước khi giải nén**:

```powershell
Test-Path .\compose.logs.yaml
Test-Path .\nginx\clinic_logging.conf
Test-Path .\monitoring\alloy\config.alloy
```

Chỉ giải nén khi cả ba là `False`. Nếu có `True`, dừng và gửi ảnh; **không dùng `-Force`** để ghi đè.

Tải file `clinic-management-step6-4-update.zip` vào Downloads và chạy:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step6-4-update.zip" -DestinationPath .
```

Kiểm tra lại ba lệnh `Test-Path` trên; cả ba cần `True`.

## 2. Kiểm tra cấu hình Docker Compose

Từ bước này, luôn dùng **5 file** để giữ lại toàn bộ thiết lập cũ.

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml config -q
```

Không hiện lỗi nghĩa là cấu hình hợp lệ. Nếu thấy lỗi, dừng và gửi ảnh.

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml config --services
```

Kết quả có `db`, `web`, `nginx`, `blackbox`, `prometheus`, `grafana`, `loki`, `alloy`.

## 3. Khởi động Loki và Alloy

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml up -d loki alloy
```

Lần đầu Docker sẽ tải 2 image mới; có thể mất vài phút. Lệnh này không xóa dữ liệu.

## 4. Áp dụng log tối giản cho Nginx

Lệnh dưới đây chỉ tạo lại container Nginx để thêm file cấu hình log và volume riêng. Cổng HTTP/HTTPS đã cấu hình ở Bước 6.1/6.2 sẽ được giữ nguyên.

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml up -d --force-recreate --no-deps nginx
```

**Không dùng `down -v`.** Việc tạo lại container Nginx có thể làm trang web gián đoạn một chút khi khởi động.

## 5. Nạp Loki vào Grafana

Vì thư mục provision của Grafana đã được gắn từ Bước 6.3, ta chỉ cần khởi động lại Grafana (không xóa dữ liệu của nó):

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml restart grafana
```

Kiểm tra trạng thái tất cả các dịch vụ:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml ps -a
```

Tám dịch vụ nên ở trạng thái `Up` (PostgreSQL có thể có thêm chữ `healthy`).

## 6. Kiểm tra Loki

Trong trình duyệt mở **http://localhost:3101/ready**. Nếu thấy `ready`, Loki đã sẵn sàng.

**Lưu ý:** Loki không có trang web dashboard tại địa chỉ này. Ta dùng Grafana để xem log.

## 7. Tạo log kiểm tra và xem trong Grafana

1. Mở **https://localhost:8443/health/** trên trình duyệt 2–3 lần để tạo yêu cầu kiểm tra an toàn.
2. Mở **http://localhost:3001/**, đăng nhập Grafana như Bước 6.3.
3. Chọn **Explore** ở thanh bên trái.
4. Tại ô chọn nguồn dữ liệu, chọn **Loki**.
5. Nếu có chế độ Builder/Code, chuyển sang **Code** và nhập LogQL:

```logql
{job="clinic_http_log"}
```

6. Chọn phạm vi thời gian **Last 15 minutes** và bấm **Run query**. Đợi vài giây.

Kết quả mong đợi là các dòng tương tự:

```text
2026-10-26T09:00:00+07:00 method=GET status=200 seconds=0.004
```

**Sẽ không thấy đường dẫn `/patients/123/`, IP hoặc tên bệnh nhân**, vì chúng ta cố ý loại khỏi dòng log lưu vào Loki.

## 8. Chẩn đoán lỗi an toàn

Nếu Loki/Alloy không chạy:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml ps -a
```

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml -f compose.monitoring.yaml -f compose.logs.yaml logs --tail=50 loki alloy
```

- `port is already allocated` tại cổng `3101`: không xóa container khác, gửi ảnh lỗi.
- Loki `not ready`: có thể cần vài giây khi khởi động; xem logs.
- Grafana thiếu Loki: xem lại Bước 5 và ảnh mục **Connections -> Data sources**.
- Không có dòng log: mở lại HTTPS `/health/`, đợi 15–30 giây, đặt **Last 15 minutes**, sau đó truy vấn lại.
- Website HTTPS không vào được: xem `docker compose ... ps -a` và `logs --tail=50 nginx`; không đụng PostgreSQL.

## 9. Lưu ý an toàn

- Dữ liệu PostgreSQL, đăng nhập, đơn thuốc và các file `.env` không bị thay đổi bởi gói ZIP này.
- Loki chỉ lắng nghe ra máy Windows ở `127.0.0.1:3101`, không có authentication riêng; **không được mở port ra Internet**.
- Loki được cấu hình lưu log tối đa khoảng **72 giờ**, sau đó quá trình compactor sẽ xóa theo lịch (không nhất thiết xóa đúng tức thì).
- Đây là một giải pháp thử nghiệm có chủ ý **không thu thập toàn bộ log Docker/Django** để giảm nguy cơ lưu thông tin y tế cá nhân; nếu muốn giám sát lỗi Django chi tiết, cần thiết kế quy tắc ẩn dữ liệu trước.
- Không chạy `docker compose down -v`: lệnh này có thể xóa volume PostgreSQL và các volume giám sát.
