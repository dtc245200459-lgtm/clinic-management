# Bước 6.1 — Thêm Nginx reverse proxy trên Windows Docker

Áp dụng cho dự án đã hoàn thành Bước 5. Bước 6 được chia nhỏ: **6.1 Nginx HTTP nội bộ → 6.2 HTTPS → 6.3 Prometheus/Grafana và Loki**.

## Cần nhớ

- Đây mới là **môi trường thực hành trên `localhost`**. Nginx trong bước này dùng **HTTP**, chưa mã hóa HTTPS và **không được xem là cấu hình triển khai thực tế trên Internet**.
- Không xóa project, `.env`, `compose.yaml`, volume PostgreSQL, hay chạy `docker compose down -v`.
- Gói ZIP chỉ bổ sung **2 file cấu hình** và tài liệu này, không ghi đè Django hoặc dữ liệu Bước 1–5.
- Máy cần chạy Docker Desktop.

## 1. Mở VS Code và PowerShell đúng thư mục

Trong VS Code mở thư mục đang có `compose.yaml`, `manage.py`, `clinic/` rồi chọn **Terminal → New Terminal** với PowerShell.

```powershell
Get-ChildItem -Name compose.yaml,manage.py,.env
```

Bạn phải thấy ba mục trên.

## 2. Kiểm tra tên file tránh ghi đè dữ liệu tùy chỉnh

```powershell
Test-Path .\compose.override.yaml
Test-Path .\nginx\default.conf
```

**Chỉ giải nén khi cả hai lệnh trả về `False`.** Nếu bất kỳ kết quả nào là `True`, **dừng và gửi ảnh cho mình** để ghép cấu hình đang có, không dùng `-Force` đè lên file tùy chỉnh.

## 3. Giải nén ZIP vào thư mục hiện tại

Tải `clinic-management-step6-1-update.zip` về thư mục Downloads, sau đó chạy:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step6-1-update.zip" -DestinationPath .
Get-ChildItem -Name compose.override.yaml
Get-ChildItem -Name .\nginx\default.conf
```

ZIP có cấu trúc:

```text
compose.override.yaml
nginx/
    default.conf
HUONG_DAN_BUOC_6_1.md
```

Không đặt chúng vào thư mục con lồng nhau. `compose.override.yaml` phải nằm **cùng cấp** với `compose.yaml`.

## 4. Kiểm tra Docker Compose nhận file bổ sung

```powershell
docker compose config --services
```

Kết quả cần có ba tên dịch vụ: `db`, `web`, `nginx` (thứ tự có thể khác).

```powershell
docker compose config -q
```

Nếu không có lỗi, tiếp tục.

## 5. Chạy Nginx

```powershell
docker compose up -d
docker compose ps
```

Bạn cần thấy `db`, `web`, `nginx` ở trạng thái chạy. Lệnh `up -d` có thể tạo lại container phù hợp nếu cấu hình thay đổi nhưng **không xóa volume PostgreSQL**.

Kiểm tra file cấu hình bên trong Nginx:

```powershell
docker compose exec nginx nginx -t
```

Kết quả mong đợi: `syntax is ok` và `test is successful`.

## 6. Mở trang web qua Nginx

Trước đây bạn truy cập: http://localhost:8000/

Bây giờ truy cập: **http://localhost:8080/**

Bạn cần thấy trang chủ phòng khám như cũ. Kiểm tra:

- http://localhost:8080/health/ — JSON `{"status":"ok"}`.
- http://localhost:8080/accounts/login/ — trang đăng nhập.
- Đăng nhập bằng tài khoản quản trị/bác sĩ/lễ tân đã có từ Bước 5.
- Trang Bệnh nhân/Lịch khám vẫn hiển thị; CSS và nút Đăng xuất hoạt động.

Thử trong PowerShell:

```powershell
Invoke-RestMethod http://localhost:8080/health/
```

Kỳ vọng có `status` là `ok`.

**Tại sao vẫn giữ `localhost:8000`?** Chặng 6.1 dùng cổng mới 8080 để kiểm tra mà không cắt đường truy cập cũ. Sau khi Nginx, HTTPS và giám sát hoạt động ổn định, chúng ta mới cân nhắc đóng cổng truy cập trực tiếp vào Django.

## 7. Cách chẩn đoán lỗi an toàn

Nếu `localhost:8080` không mở được:

```powershell
docker compose ps
docker compose logs --tail=80 nginx
docker compose logs --tail=80 web
```

- `port is already allocated` / cổng 8080 đang dùng: dừng ở đây, báo mình; không tùy ý xóa container khác.
- `502 Bad Gateway`: Nginx đã chạy nhưng chưa kết nối tới Django; kiểm tra `web` và logs.
- `403 CSRF verification failed` khi gửi form qua Nginx: gửi ảnh và log; đừng tắt CSRF. Cấu hình đã cố ý giữ nguyên Host kèm cổng.
- `nginx: configuration file ... test failed`: gửi kết quả `docker compose exec nginx nginx -t`.

Muốn tạm thời dùng đường truy cập cũ, bạn vẫn có thể mở http://localhost:8000/; **không cần xóa** bất kỳ file hay volume nào.

## 8. Vì sao chọn cách này?

Docker Compose tự ghép `compose.yaml` và `compose.override.yaml`, do đó file tùy chỉnh Gunicorn và dữ liệu cũ được giữ. Nginx nhận HTTP trên cổng 8080 của máy Windows và chuyển tiếp yêu cầu đến service `web:8000` trong mạng Docker. Không có migration Django mới ở Bước 6.1.

Sau khi bạn kiểm tra thành công, chặng **6.2** sẽ bổ sung HTTPS *phát triển cục bộ* mà không chia sẻ khóa bí mật trong ZIP. Chặng **6.3** sẽ bổ sung Prometheus/Grafana và Loki với cấu hình tránh thu thập dữ liệu bệnh nhân thật.
