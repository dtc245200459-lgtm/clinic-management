# Bước 6.2 — HTTPS thử nghiệm trên Windows + Docker Compose

## Mục tiêu

Giữ trang cũ **http://localhost:8081/** làm dự phòng, bổ sung **https://localhost:8443/**.
Không thay `compose.yaml`, `compose.override.yaml`, `.env`, `nginx/default.conf`, `config/settings.py`, không xóa database hay volume.

Chứng chỉ tự ký sẽ được **tạo trên máy của bạn**, không có private key đính kèm gói ZIP. Trình duyệt sẽ cảnh báo chứng chỉ chưa được tin cậy; đó là bình thường cho môi trường học tập. **Tuyệt đối không dùng bệnh án thật**.

## 1. Mở đúng PowerShell trong VS Code

Mở thư mục đang chứa `compose.yaml`, `compose.override.yaml`, `manage.py`. Chạy:

```powershell
Test-Path .\compose.yaml
Test-Path .\compose.override.yaml
Test-Path .\nginx\default.conf
```

Tất cả cần là `True`.

## 2. Kiểm tra trước khi giải nén

```powershell
Test-Path .\compose.https.yaml
Test-Path .\nginx\https.conf
Test-Path .\config\settings_https.py
```

**Chỉ tiếp tục nếu cả ba đều `False`**. Nếu có `True`, gửi ảnh cho mình để tránh ghi đè nội dung bạn đã làm.

Tải `clinic-management-step6-2-update.zip`, để trong Downloads và chạy:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step6-2-update.zip" -DestinationPath .
```

## 3. Tạo chứng chỉ thử nghiệm 30 ngày bằng Docker

```powershell
New-Item -ItemType Directory -Force -Path .\nginx\certs
```

```powershell
docker run --rm -v "${PWD}\nginx\certs:/certs" alpine/openssl req -x509 -nodes -days 30 -newkey rsa:2048 -keyout /certs/localhost.key -out /certs/localhost.crt -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

Lần đầu chạy Docker có thể tải ảnh `alpine/openssl`. Nếu màn hình in nhiều dấu `+` và không có `error`, có thể là đã tạo xong. Xác minh:

```powershell
Test-Path .\nginx\certs\localhost.crt
Test-Path .\nginx\certs\localhost.key
```

Cả hai cần `True`. **Không chia sẻ `localhost.key`, không đưa thư mục `nginx/certs/` lên GitHub.** Nếu dùng Git, thêm dòng `nginx/certs/` vào `.gitignore` tại dự án Windows.

## 4. Kiểm tra Compose và chạy HTTPS

Từ bước này, mọi lệnh dùng **đủ ba file** `-f` như dưới đây; `compose.https.yaml` không được Docker tự tải khi chạy `docker compose` trần.

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml config -q
```

Nếu không in lỗi, chạy:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml up -d --build web nginx
```

Lệnh này có thể xây dựng lại ứng dụng và tạo lại container `web`/`nginx` nếu cần, **không xóa volume PostgreSQL**. Có thể mất vài phút ở lần đầu.

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml ps -a
```

Kiểm tra cấu hình nginx:

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml exec nginx nginx -t
```

Kết quả mong đợi `syntax is ok` và `test is successful`.

## 5. Mở và kiểm tra

1. Mở **https://localhost:8443/** (chữ **s** trong `https` là quan trọng).
2. Trình duyệt thường hiện cảnh báo chứng chỉ tự ký. Chỉ tiếp tục nếu bạn chắc chắn đang ở chính `localhost` của máy mình; **không** nhập dữ liệu thật. Không cần cài chứng chỉ vào kho tin cậy toàn hệ thống.
3. Đăng nhập tài khoản thử nghiệm, mở Bệnh nhân / Bác sĩ / Lịch khám.
4. Thử một biểu mẫu dữ liệu **giả** để xác nhận không có lỗi `403 CSRF`.
5. Kiểm tra `http://localhost:8081/` vẫn hoạt động như dự phòng.

## 6. Nếu có lỗi

```powershell
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml ps -a
docker compose -f compose.yaml -f compose.override.yaml -f compose.https.yaml logs --tail=50 nginx web
```

- `port is already allocated` với `8443`: dừng, gửi ảnh; không tự xóa container khác.
- `cannot load certificate`: kiểm tra hai file ở bước 3 và đường dẫn thư mục.
- `502 Bad Gateway`: kiểm tra `web` đã `Up` chưa.
- `403 CSRF`: chắc chắn truy cập qua `https://localhost:8443/`, không trộn với HTTP hoặc tab cũ; gửi ảnh lỗi.
- Trình duyệt cảnh báo `NET::ERR_CERT_AUTHORITY_INVALID`: dự kiến với chứng chỉ tự ký, không phải lỗi Nginx.

### Lưu ý

Đây là HTTPS **phục vụ học tập trên localhost**, chưa phải triển khai Internet hoặc cấu hình bảo mật hoàn chỉnh. Khi đi vào môi trường thực tế, cần tên miền/chứng chỉ tin cậy, tắt DEBUG, đặt cookie bảo mật, giới hạn truy cập Gunicorn, bảo vệ backup và dữ liệu cá nhân.

**Tuyệt đối tránh `docker compose down -v` vì sẽ xóa dữ liệu trong volume.**
