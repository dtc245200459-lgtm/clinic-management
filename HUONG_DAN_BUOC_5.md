# BƯỚC 5 — Đăng nhập, đăng xuất và phân quyền

Áp dụng khi bạn đã hoàn thành **Bước 4** với Django, PostgreSQL và Docker Compose.

## 0. GHI NHỚ TRƯỚC KHI CẬP NHẬT

- **Không xóa thư mục dự án cũ**, database PostgreSQL hoặc volume Docker.
- **Không chạy `docker compose down -v`** hay `docker volume rm`.
- Gói ZIP **không chứa** `.env`, `compose.yaml`, `Dockerfile`, migration `0001`–`0003`.
- Bạn vẫn dùng tài khoản superuser (quản trị viên) hiện tại và dữ liệu bệnh nhân/bác sĩ/lịch hẹn/hồ sơ/đơn thuốc cũ.
- Phần mềm đang ở mức thực hành; chỉ nhập dữ liệu bệnh nhân và thuốc **giả lập**. Hệ thống chưa đủ điều kiện bảo vệ hồ sơ sức khỏe thật.

## 1. MỞ ĐÚNG TERMINAL POWERSHELL TRONG VS CODE

1. Mở **VS Code → File → Open Folder**.
2. Chọn thư mục dự án **đang chứa `manage.py`, `compose.yaml`, `clinic`**.
3. Chọn **Terminal → New Terminal**, sử dụng **PowerShell**.
4. Kiểm tra:

```powershell
Get-ChildItem -Name manage.py,compose.yaml,.env,clinic,templates,config
```

Phải có đủ 6 mục. Không tạo dự án Django mới.

## 2. SAO LƯU MÃ NGUỒN TRƯỚC KHI GIẢI NÉN

```powershell
$backupName = "backup-code-buoc4-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
Compress-Archive -Path .\clinic,.\config,.\templates -DestinationPath ".\$backupName"
Get-ChildItem ".\$backupName"
```

Đây mới là **bản sao lưu mã nguồn**. Nếu dữ liệu PostgreSQL quan trọng, bạn cần sao lưu database riêng trước khi cập nhật.

## 3. GIẢI NÉN BỘ MÃ NGUỒN BƯỚC 5

Tải `clinic-management-step5-update.zip` về **Downloads**. Trong VS Code PowerShell đang ở thư mục dự án, chạy:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step5-update.zip" -DestinationPath . -Force
Get-ChildItem .\clinic\migrations\0004_*.py
Get-ChildItem .\templates\clinic\login.html
```

**Chú ý:** Lệnh `-Force` cập nhật những file mã nguồn cũ (`clinic/views.py`, `clinic/tests.py`, `templates/clinic/base.html`, v.v.). Nếu bạn đã tự sửa chúng sau Bước 4, hãy so sánh với bản sao lưu rồi hợp nhất thay đổi trước khi giải nén. `compose.yaml` và `.env` không nằm trong gói ZIP.

## 4. CHẠY DOCKER VÀ MIGRATION MỚI

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

Kết quả `showmigrations clinic` cần có:

```text
 [X] 0001_initial
 [X] 0002_doctor_appointment
 [X] 0003_medicalrecord_medicine_prescription_prescriptionitem
 [X] 0004_doctor_user_roles
```

`python manage.py check` phải không báo lỗi. `python manage.py test clinic` dự kiến hiện **`Ran 57 tests`**, **`OK`**.

> Migration `0004` thêm một cột `user_id` **cho phép trống** vào bảng bác sĩ và tạo hai nhóm quyền `Bác sĩ`, `Lễ tân`. Không xóa/sửa hồ sơ bệnh nhân, lịch hẹn hay đơn thuốc hiện có.

## 5. ĐĂNG NHẬP QUẢN TRỊ VIÊN CŨ

- Đăng nhập giao diện nghiệp vụ: http://localhost:8000/accounts/login/
- Đăng nhập Django Admin: http://localhost:8000/admin/
- Dùng **tên đăng nhập và mật khẩu superuser cũ**. Không cần `createsuperuser` lần nữa.

**Quan trọng:** Trong Bước 5, chỉ **superuser** có quyền Quản trị viên trên giao diện nghiệp vụ. Nếu có tài khoản cũ chỉ bật `Staff status` mà không có `Superuser status`, tài khoản đó sẽ phải được gán nhóm phù hợp trước khi sử dụng nghiệp vụ mới; hệ thống **không tự nâng quyền**.

## 6. TẠO TÀI KHOẢN LỄ TÂN

1. Tại `http://localhost:8000/admin/`, mở **Authentication and Authorization → Users → Add user**.
2. Đặt **Username** ví dụ `letan01`; nhập mật khẩu đủ mạnh và xác nhận. Không chia sẻ mật khẩu qua ảnh chụp.
3. Nhấn **Save and continue editing** hoặc lưu rồi mở lại tài khoản.
4. Trong phần **Permissions**:
   - `Active`: **bật**.
   - `Staff status`: **không bật**.
   - `Superuser status`: **không bật**.
   - Trong **Groups**, chọn **Lễ tân** (chọn một nhóm duy nhất).
5. Nhấn **Save**.

Lễ tân đăng nhập tại `http://localhost:8000/accounts/login/`. Họ được quản lý bệnh nhân/lịch hẹn, xem danh sách bác sĩ; không có quyền vào hồ sơ khám hay đơn thuốc.

## 7. TẠO TÀI KHOẢN BÁC SĨ VÀ GẮN VỚI BÁC SĨ HIỆN CÓ

**Bước A — Tạo user**

1. Vào Django Admin → **Users → Add user**.
2. Tạo `bacsi01` với mật khẩu đủ mạnh.
3. `Active`: **bật**; `Staff status`, `Superuser status`: **không bật**.
4. Gán đúng **một nhóm Bác sĩ**. **Save**.

**Bước B — Liên kết user với bác sĩ**

1. Trong Django Admin, mở **Clinic → Bác sĩ (Doctors)**.
2. Chọn bác sĩ đã có (ví dụ `BS001`), hoặc thêm một bác sĩ demo nếu chưa có.
3. Ở trường **Tài khoản đăng nhập**, chọn `bacsi01`.
4. Nhấn **Save**.

**Nếu bỏ qua Bước B**, bác sĩ có thể đăng nhập nhưng **không thể tạo hồ sơ khám** vì hệ thống chưa biết tài khoản này thuộc bác sĩ nào.

## 8. THỬ PHÂN QUYỀN TRÊN TRÌNH DUYỆT

**Tài khoản Quản trị viên (superuser):**

- Đăng nhập `http://localhost:8000/accounts/login/`.
- Có các mục Bệnh nhân, Bác sĩ, Lịch khám, Hồ sơ khám, Thuốc, Quản trị.
- Có thể vào `http://localhost:8000/admin/auth/user/` để quản lý người dùng.

**Tài khoản Lễ tân (`letan01`):**

- Đăng nhập, thấy **Bệnh nhân**, **Bác sĩ**, **Lịch khám**.
- Thử mở `http://localhost:8000/records/`: phải hiện **403 Không có quyền truy cập**.
- Thử thêm bệnh nhân giả lập, đặt lịch demo.

**Tài khoản Bác sĩ (`bacsi01`):**

- Đăng nhập, thấy **Bác sĩ**, **Lịch khám**, **Hồ sơ khám**, **Thuốc**.
- Lịch và hồ sơ chỉ hiển thị những trường hợp thuộc bác sĩ được gắn tài khoản.
- Có thể tạo hồ sơ khám và đơn thuốc cho **lịch của mình**, xem danh mục thuốc.
- Thử mở `http://localhost:8000/patients/`: phải hiện **403 Không có quyền truy cập**.
- Không thể sửa danh mục thuốc; không thể xem đơn thuốc của bác sĩ khác bằng cách đoán URL.

### Đăng xuất

Ở thanh menu, bấm nút **Đăng xuất**. Đăng xuất sử dụng biểu mẫu **POST có CSRF**; không cần gõ URL `/accounts/logout/` trực tiếp vào trình duyệt.

## 9. CÁC FILE ĐƯỢC THÊM / CẬP NHẬT

| File | Chức năng |
| --- | --- |
| `clinic/permissions.py` | Kiểm soát nhóm và trả về HTTP 403 khi không có quyền |
| `clinic/models.py` | Thêm liên kết 1–1 giữa bác sĩ và tài khoản |
| `clinic/migrations/0004_doctor_user_roles.py` | Thêm cột nullable và tạo nhóm quyền |
| `clinic/views.py` | Phân quyền từng chức năng, lọc dữ liệu theo bác sĩ |
| `clinic/forms.py` | Giới hạn lịch hẹn có thể chọn theo bác sĩ đăng nhập |
| `clinic/admin.py` | Cho phép quản trị viên liên kết user với bác sĩ |
| `config/urls.py`, `config/settings.py` | Đăng nhập/đăng xuất và cấu hình điều hướng |
| `templates/clinic/login.html`, `templates/403.html` | Trang đăng nhập và thông báo thiếu quyền |
| `templates/clinic/base.html`, `templates/clinic/home.html` | Menu theo nhóm quyền và nút Đăng xuất |
| `clinic/tests.py` | Bộ kiểm thử truy cập theo vai trò |

## 10. XỬ LÝ LỖI THƯỜNG GẶP

- `No migrations to apply`: bình thường nếu `0004` đã đánh dấu `[X]`.
- Không thấy nhóm `Bác sĩ` hoặc `Lễ tân`: kiểm tra `showmigrations clinic`, đảm bảo `0004` có `[X]`.
- Không thấy trường `Tài khoản đăng nhập` ở màn hình sửa bác sĩ: xác nhận ZIP đã giải nén và Docker đã được `up -d --build`.
- Bác sĩ thấy trang **403** khi tạo hồ sơ: kiểm tra đã gán Group `Bác sĩ` và đã liên kết tại **Clinic → Bác sĩ**.
- Bác sĩ không thấy lịch khám: lịch hiện có của bác sĩ **khác**, hoặc hồ sơ bác sĩ chưa gắn đúng tài khoản.
- Lễ tân nhận **403** khi mở hồ sơ/đơn thuốc: **đúng thiết kế phân quyền**.
- `Session data corrupted`: thử đăng xuất/đăng nhập lại; giữ nguyên `DJANGO_SECRET_KEY` trong `.env`. Không xóa PostgreSQL để sửa lỗi phiên đăng nhập.
- Lỗi không rõ: chạy `docker compose logs --tail=100 web`, gửi ảnh hoặc sao chép traceback.

Sau bước này, dự án đã có phân quyền cơ bản. Trước khi sử dụng dữ liệu bệnh nhân thật hoặc triển khai Internet, cần bổ sung HTTPS, phân quyền hồ sơ chi tiết hơn, audit log, sao lưu/khôi phục và chính sách bảo mật.
