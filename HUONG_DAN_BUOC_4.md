# Bước 4 — Hồ sơ khám, danh mục thuốc và đơn thuốc

Áp dụng cho dự án **Django + PostgreSQL + Docker Compose** đã hoàn thành Bước 3.

## CẢNH BÁO QUAN TRỌNG

- Bản cập nhật này **không** có `compose.yaml`, `.env`, `Dockerfile`, migration `0001` hay `0002`.
- Giữ nguyên **thư mục dự án hiện tại** và volume PostgreSQL. Tuyệt đối không chạy `docker compose down -v` hoặc `docker volume rm`.
- Trước khi giải nén đè, hãy sao lưu mã nguồn và nếu đang có dữ liệu quý, sao lưu thêm PostgreSQL.
- Đây là dự án học tập. **Chỉ sử dụng bệnh nhân, chẩn đoán, thuốc và liều dùng giả lập.** Chức năng đơn thuốc không đưa ra gợi ý điều trị.

## 1. Mở đúng Terminal và đúng thư mục

1. Mở **VS Code** → **File → Open Folder** → chọn thư mục dự án đang chứa `compose.yaml`, `manage.py`, `clinic`, `templates`.
2. Bấm **Terminal → New Terminal**.
3. Chọn **PowerShell** từ menu mũi tên cạnh dấu `+` nếu đang mở terminal khác.
4. Kiểm tra thư mục hiện tại bằng:

```powershell
Get-Location
Get-ChildItem -Name compose.yaml,manage.py,clinic,templates,.env
```

Lệnh thứ hai phải liệt kê đủ 5 mục. Nếu không, hãy dùng `cd "C:\duong-dan\den\du-an-cua-ban"` và kiểm tra lại.

## 2. Sao lưu trước khi thay mã nguồn

```powershell
$backupName = "backup-code-buoc3-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
Compress-Archive -Path .\clinic,.\templates -DestinationPath ".\$backupName"
Get-ChildItem ".\$backupName"
```

Lệnh trên sao lưu *mã nguồn*. Nếu đang dùng dữ liệu quan trọng, hãy sao lưu cơ sở dữ liệu PostgreSQL riêng trước khi cập nhật.

## 3. Cập nhật từ ZIP

1. Tải `clinic-management-step4-update.zip` từ ChatGPT về thư mục **Downloads**.
2. Trong terminal VS Code PowerShell (đang ở thư mục dự án):

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step4-update.zip" -DestinationPath . -Force
Get-ChildItem .\clinic\migrations\0003_*.py
Get-ChildItem .\templates\clinic\*prescription*.html
```

Lưu ý: `-Force` sẽ ghi đè **một số file mã nguồn** Bước 1–3 như `clinic/views.py`, `clinic/forms.py`, `clinic/tests.py`. Nếu bạn đã tự sửa các file này, hãy đối chiếu với bản sao lưu thay vì chép đè ngay. **Không xóa file cũ** hoặc thay cả dự án.

## 4. Khởi chạy lại Docker, tạo bảng mới

```powershell
docker compose config -q
docker compose up -d --build
docker compose ps
docker compose exec web python manage.py migrate
docker compose exec web python manage.py showmigrations clinic
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py test clinic
```

Kết quả mong đợi:

- `showmigrations clinic` có `[X] 0001_initial`, `[X] 0002_doctor_appointment`, `[X] 0003_medicalrecord_medicine_prescription_prescriptionitem`.
- `check`: `System check identified no issues`.
- `makemigrations --check --dry-run`: `No changes detected`.
- `test clinic`: `Ran 40 tests` và `OK`.

Nếu chạy Docker lỗi: xem log bằng `docker compose logs --tail=100 web` và gửi nguyên dòng lỗi, nhất là dòng cuối cùng.

## 5. Kiểm tra bằng trình duyệt

Đăng nhập tài khoản quản trị/staff ở [http://localhost:8000/admin/](http://localhost:8000/admin/), sau đó thử:

1. [http://localhost:8000/appointments/](http://localhost:8000/appointments/) — cần ít nhất một lịch **Chờ khám** hoặc **Đã khám** chưa có hồ sơ, **không phải Đã hủy**. Nếu tất cả đã hủy, bấm **Đặt lịch khám** để thêm lịch demo.
2. [http://localhost:8000/records/new/](http://localhost:8000/records/new/) — chọn lịch hẹn, nhập "Triệu chứng demo", "Chẩn đoán demo", "Hướng xử trí demo" và bấm **Lưu hồ sơ**.
3. [http://localhost:8000/records/](http://localhost:8000/records/) — xuất hiện hồ sơ mới. Kiểm tra lịch liên quan đã chuyển sang **Đã khám**.
4. [http://localhost:8000/medicines/new/](http://localhost:8000/medicines/new/) — tạo thuốc giả lập, ví dụ **Thuốc mẫu A**, đơn vị **viên**.
5. Mở hồ sơ vừa tạo → **Tạo đơn thuốc** → nhập ghi chú → **Lưu đơn thuốc**.
6. Trong trang đơn thuốc, bấm **Thêm dòng thuốc** → chọn thuốc mẫu, nhập số lượng như `2` và nội dung cách dùng **giả lập** → **Lưu dòng thuốc**.
7. Thử thêm thuốc trùng trong cùng đơn: hệ thống phải báo đã có dòng thuốc. Thử số lượng `0`: hệ thống phải báo lỗi. Bạn cũng có thể bấm **Sửa** dòng thuốc.

Địa chỉ chức năng:

| Chức năng | URL |
| --- | --- |
| Danh sách hồ sơ | `/records/` |
| Tạo hồ sơ | `/records/new/` |
| Danh mục thuốc | `/medicines/` |
| Thêm thuốc | `/medicines/new/` |
| Tạo đơn thuốc | Nút trên trang chi tiết hồ sơ |
| Thêm dòng thuốc | Nút trên trang chi tiết đơn thuốc |

## 6. Các bảng mới trong PostgreSQL

Migration `0003` chỉ **tạo thêm**:

- `clinic_medicalrecord`: một hồ sơ khám gắn với một lịch hẹn;
- `clinic_medicine`: danh mục thuốc;
- `clinic_prescription`: một đơn thuốc gắn với một hồ sơ;
- `clinic_prescriptionitem`: mỗi dòng thuốc trong đơn, có số lượng/liều dùng/v.v.

Các bảng `clinic_patient`, `clinic_doctor`, `clinic_appointment` và dữ liệu hiện có **không bị xóa hay tạo lại**.

## 7. Nếu có lỗi

- `No such table clinic_medicalrecord`: kiểm tra `showmigrations` và chạy `docker compose exec web python manage.py migrate`.
- `No migrations to apply`: bình thường nếu migration 0003 đã áp dụng.
- Dropdown lịch hẹn trống: lịch demo đã hủy hoặc đã có hồ sơ; tạo lịch chưa hủy mới.
- Trang web vẫn hiển thị phiên bản cũ: dùng **Ctrl+F5**, xem `docker compose logs --tail=80 web`.
- `command not found` hay `No such service: web`: kiểm tra bạn đang ở thư mục chứa `compose.yaml`, và tên dịch vụ Docker của bạn thực sự là `web`.

Đến đây là hoàn thành **Bước 4**. Bước tiếp theo có thể bổ sung tài khoản nhân viên và phân quyền cụ thể theo vai trò, trước khi triển khai giám sát/nghiệp vụ nâng cao.
