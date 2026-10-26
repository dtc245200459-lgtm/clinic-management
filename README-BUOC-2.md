# Bước 2 – Quản lý bệnh nhân (Windows + VS Code + Docker)

Gói `clinic-management-step2-update.zip` cập nhật dự án **Bước 1** đang chạy của bạn. **Không cần tạo dự án mới**, không cần xóa database, không cần tạo lại tài khoản admin. Gói này **không chứa `.env` hoặc `compose.yaml`**.

## 1. Cập nhật code vào đúng thư mục

1. Tải `clinic-management-step2-update.zip` xuống thư mục Downloads của Windows.
2. Mở VS Code với thư mục `clinic-management-starter` đang chạy (chứa `compose.yaml` và `.env`).
3. Mở **Terminal → New Terminal**, loại **PowerShell**.
4. Xác nhận đang ở đúng thư mục:

```powershell
Get-ChildItem -Force compose.yaml, .env
```

5. Nếu bạn chưa chỉnh sửa mã nguồn ngoài phần `.env`, chạy lệnh sau để chép các file Bước 2 vào đúng vị trí:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step2-update.zip" -DestinationPath . -Force
```

> Lưu ý: `-Force` sẽ ghi đè các file mã nguồn trùng tên như `clinic/views.py`, `clinic/models.py` và `clinic/tests.py`. Nếu bạn đã tự sửa các file này, hãy sao lưu chúng trước. Lệnh không thay đổi `.env` và không xóa volume PostgreSQL.

6. Kiểm tra file mới:

```powershell
Get-ChildItem .\clinic\forms.py, .\clinic\migrations\0001_initial.py, .\templates\clinic\patient_list.html
```

## 2. Docker cập nhật code và database

Chạy lần lượt:

```powershell
docker compose config -q
docker compose up -d --build
docker compose ps
```

`web` sẽ chạy migration đã có trong `clinic/migrations/0001_initial.py` trước khi Gunicorn khởi động. Không chạy `docker compose down -v` vì lệnh đó xóa volume database của project.

## 3. Kiểm tra migrations và chức năng

```powershell
docker compose exec web python manage.py showmigrations clinic
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py check
docker compose exec web python manage.py test clinic
```

Kết quả kỳ vọng:

- `showmigrations clinic`: `[X] 0001_initial`.
- `makemigrations --check --dry-run`: `No changes detected`.
- `check`: `System check identified no issues`.
- `test clinic`: 10 bài kiểm thử thành công (`OK`).

## 4. Thử trên trình duyệt

1. Truy cập <http://localhost:8000/patients/>.
2. Nếu chưa đăng nhập, hệ thống sẽ chuyển đến trang đăng nhập admin. Dùng **tài khoản superuser đã tạo ở Bước 1**.
3. Nhấn **+ Thêm bệnh nhân**.
4. Nhập **dữ liệu giả lập**: Mã `BN001`, Họ tên `Nguyễn Văn An`, điện thoại thử `0901234567`, ngày sinh tự chọn trong quá khứ.
5. Nhấn **Lưu bệnh nhân**. Mã `BN001` sẽ hiện ở danh sách.
6. Tìm `BN001` hoặc `Nguyễn Văn An` ở thanh tìm kiếm.
7. Bấm **Sửa** để đổi số điện thoại, lưu và kiểm tra lại.
8. Bấm **Xóa**, đọc màn hình xác nhận, chỉ xác nhận với dữ liệu demo.

Bạn cũng có thể truy cập <http://localhost:8000/admin/> và kiểm tra mục **Bệnh nhân** trong Django Admin.

## 5. File nào làm gì?

| File | Nhiệm vụ |
| --- | --- |
| `clinic/models.py` | Định nghĩa bảng `Patient` gồm mã, họ tên, ngày sinh, giới tính, liên hệ |
| `clinic/migrations/0001_initial.py` | Khai báo tạo bảng trong PostgreSQL |
| `clinic/forms.py` | Form nhập/sửa, mã bệnh nhân tự chuyển chữ hoa, kiểm tra ngày sinh |
| `clinic/views.py` | Truy vấn danh sách, tìm kiếm, thêm, sửa, xóa qua POST |
| `clinic/urls.py` | Đăng ký đường dẫn `/patients/`, `/patients/new/`, ... |
| `clinic/admin.py` | Đăng ký model để quản lý qua `/admin/` |
| `clinic/tests.py` | Kiểm tra các tình huống thành công, trùng mã, sai ngày sinh, quyền truy cập |
| `templates/clinic/base.html` | Thanh điều hướng và giao diện chung |
| `templates/clinic/patient_list.html` | Bảng danh sách và tìm kiếm |
| `templates/clinic/patient_form.html` | Biểu mẫu thêm/sửa |
| `templates/clinic/patient_confirm_delete.html` | Xác nhận trước khi xóa |
| `templates/clinic/home.html` | Thêm nút đi đến quản lý bệnh nhân |
| `clinic/static/clinic/styles.css` | Giao diện và bố cục |

## 6. Nếu gặp lỗi

Chạy:

```powershell
docker compose logs --tail=100 web
docker compose logs --tail=100 db
```

Gửi ảnh màn hình phần lỗi (không gửi `.env`, mật khẩu, token, hoặc dữ liệu bệnh nhân thật) để mình hỗ trợ.

## 7. Phạm vi bảo mật hiện tại

- Mọi trang quản lý bệnh nhân tạm thời yêu cầu tài khoản **staff**; superuser từ Bước 1 đáp ứng yêu cầu này. Phân quyền bác sĩ/lễ tân riêng sẽ làm ở giai đoạn sau.
- Mã bệnh nhân là duy nhất. Xóa cần trang xác nhận và yêu cầu POST kèm CSRF token.
- Chức năng xóa chỉ phù hợp với **dữ liệu thực hành**. Khi mở rộng hồ sơ khám, cần thiết kế lưu lịch sử và chính sách không xóa dữ liệu y tế tùy tiện.
- Dự án vẫn chỉ chạy local cho mục tiêu học tập, chưa đủ điều kiện lưu trữ hồ sơ bệnh nhân thật.
