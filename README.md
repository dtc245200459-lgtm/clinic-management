# Hệ thống quản lý phòng khám – Bước 1

Đây là bộ khung **Django 5.2 LTS + PostgreSQL 16 + Docker Compose** dành cho đồ án *Triển khai và Quản trị Hệ thống Phần mềm*. Bước này chưa có dữ liệu bệnh nhân hoặc chức năng khám bệnh; mục tiêu là chứng minh ứng dụng và cơ sở dữ liệu kết nối được.

## 1. Chuẩn bị

- Cài **Docker Desktop** (Windows/macOS) hoặc **Docker Engine + Compose plugin** (Ubuntu).
- Cài **Visual Studio Code** để sửa mã nguồn.
- Mở Docker Desktop và chờ Engine chạy nếu bạn đang dùng Windows.
- Kiểm tra tại Terminal / PowerShell:

```bash
docker --version
docker compose version
```

Tài liệu cài Docker chính thức: <https://docs.docker.com/get-docker/>.

## 2. Mở thư mục dự án

Giải nén `clinic-management-starter.zip`. Trong VS Code chọn **File → Open Folder** và mở thư mục `clinic-management-starter` (thư mục có `compose.yaml`). Mở **Terminal → New Terminal**.

Tạo tệp `.env` từ `.env.example`:

- Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

- Ubuntu / macOS:

```bash
cp .env.example .env
```

Mở `.env` và **thay hai giá trị** `POSTGRES_PASSWORD` và `DJANGO_SECRET_KEY` bằng chuỗi bí mật do bạn tự tạo. Không gửi nội dung `.env` cho người khác và không đưa tệp đó lên GitHub.

## 3. Khởi chạy

Chạy lần lượt từ thư mục có `compose.yaml`:

```bash
docker compose config
docker compose up -d --build
docker compose ps
```

Lần đầu tải image và cài các thư viện nên có thể mất vài phút. Mở:

- Website: <http://localhost:8000/>
- Kiểm tra kết nối database: <http://localhost:8000/health/>
- Quản trị Django: <http://localhost:8000/admin/>

Tại trang chủ, bạn sẽ thấy thông báo PostgreSQL đã kết nối nếu ứng dụng truy vấn `SELECT 1` thành công. `/health/` trả về `{"status": "ok"}`.

**Lưu ý:** Cổng 8000 chỉ được mở trên `127.0.0.1` để giảm rủi ro trong giai đoạn phát triển. Nếu bạn chạy Docker trong máy ảo Ubuntu và muốn truy cập từ máy Windows khác, hãy báo mình để cấu hình đường truy cập phù hợp; chưa nên mở dữ liệu nhạy cảm lên mạng.

## 4. Kiểm tra ứng dụng

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test clinic
docker compose logs --tail=50 web
```

Tạo tài khoản quản trị (bạn tự đặt tên đăng nhập và mật khẩu):

```bash
docker compose exec web python manage.py createsuperuser
```

Sau đó đăng nhập tại <http://localhost:8000/admin/>. Lúc này trang admin chủ yếu có quản lý tài khoản; các bảng nghiệp vụ sẽ được bổ sung ở Bước 2.

## 5. Các lệnh Docker cần nhớ

| Lệnh | Ý nghĩa |
| --- | --- |
| `docker compose ps` | Xem container nào đang chạy |
| `docker compose logs -f web` | Xem log web liên tục; bấm Ctrl+C để thoát |
| `docker compose logs --tail=50 db` | Xem 50 dòng log cuối của PostgreSQL |
| `docker compose down` | Dừng hệ thống, giữ nguyên dữ liệu PostgreSQL |
| `docker compose up -d --build` | Xây dựng lại và khởi chạy sau khi sửa code |

**Không dùng `docker compose down -v` khi muốn giữ dữ liệu:** cờ `-v` xóa cả volume cơ sở dữ liệu.

## 6. Vì sao có những file này?

- `Dockerfile`: cách tạo image Python và cài Django/Gunicorn.
- `compose.yaml`: khai báo container `web`, `db`, mạng và volume.
- `.env.example`: mẫu cấu hình; file `.env` thật được giữ riêng.
- `config/settings.py`: cấu hình Django, kết nối PostgreSQL.
- `clinic/`: app nghiệp vụ; các model sẽ được tạo trong bước tiếp theo.
- `templates/clinic/home.html`: giao diện kiểm tra lần đầu.

## 7. Kết quả cần đạt trước khi làm tiếp

- [ ] `docker compose ps` cho thấy `db` khỏe và `web` đang chạy.
- [ ] Trang `http://localhost:8000/` hiển thị giao diện phòng khám.
- [ ] Trang `/health/` trả về `status: ok`.
- [ ] `python manage.py check` không báo lỗi.
- [ ] 2 bài kiểm thử `clinic` chạy thành công.

Bước 2 sẽ xây dựng **Patient, Doctor, Appointment** bằng Django models, migration, Django admin và giao diện quản lý cơ bản. Các phần Nginx/HTTPS, pgAdmin, Prometheus/Grafana và Loki/Promtail được thêm theo giai đoạn để phù hợp báo cáo.

Đây chỉ là môi trường **học tập/demo**, không phải phần mềm y tế đủ điều kiện lưu trữ hồ sơ thật.
