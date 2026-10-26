# Bước 3 – Quản lý bác sĩ và lịch hẹn (Windows, VS Code, Docker)

Gói `clinic-management-step3-update.zip` được thiết kế để **cập nhật trực tiếp dự án Bước 2** đang chạy thành công. Không tạo thư mục dự án Docker khác; không xóa `.env`, `compose.yaml`, database hoặc tài khoản quản trị.

## 1. Những chức năng mới

- Quản lý bác sĩ: thêm, sửa, tìm theo mã/tên/chuyên khoa, đánh dấu ngừng làm việc mà không xóa lịch sử.
- Lịch hẹn: chọn bệnh nhân đã có, bác sĩ đang làm việc, ngày giờ và lý do khám; tìm kiếm/lọc lịch hẹn; sửa lịch; đánh dấu đã khám hoặc hủy lịch.
- Ngăn đặt hai lịch **chưa hủy** cho cùng một bác sĩ tại **cùng thời điểm chính xác**.
- Không cho đặt lịch chờ khám mới trong quá khứ.
- Không xóa bệnh nhân đã có lịch hẹn (để giữ quan hệ lịch sử).

Đây là demo đơn giản. Chức năng chống trùng lịch mới so sánh cùng thời điểm; chưa quản lý thời lượng khám, ngày nghỉ và ca làm việc.

## 2. Cập nhật vào đúng thư mục cũ

1. Tải `clinic-management-step3-update.zip` vào thư mục Downloads trên Windows.
2. Trong VS Code, mở **thư mục cũ** `clinic-management-starter` đang chứa `compose.yaml` và `.env`.
3. Mở Terminal PowerShell và xác nhận:

```powershell
Get-ChildItem -Force compose.yaml, .env
Test-Path "$env:USERPROFILE\Downloads\clinic-management-step3-update.zip"
```

Lệnh `Test-Path` phải hiện `True`. Nếu file tải về có tên `(1)` hoặc nằm ở nơi khác, đổi đường dẫn cho đúng.

4. Nếu đã tự sửa các file mã nguồn của Bước 2, hãy sao lưu trước. Có thể tạo một bản nén code:

```powershell
Compress-Archive -Path .\clinic, .\templates -DestinationPath .\backup-code-buoc2.zip
```

5. Chép các file của Bước 3 vào đúng thư mục:

```powershell
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\clinic-management-step3-update.zip" -DestinationPath . -Force
```

> `-Force` ghi đè những file code trùng tên như `clinic/models.py`, `clinic/views.py`, `clinic/forms.py` và templates. Gói ZIP không chứa `.env`, không chứa `compose.yaml`, không chứa hoặc sửa migration `0001_initial.py`. Không ảnh hưởng đến volume PostgreSQL.

6. Kiểm tra file migration mới:

```powershell
Get-ChildItem .\clinic\migrations\0002_doctor_appointment.py
```

## 3. Khởi động lại hệ thống

```powershell
docker compose config -q
docker compose up -d --build
docker compose ps
```

Lệnh khởi động web của Bước 1 vốn có `python manage.py migrate --noinput`, vì vậy migration mới sẽ tự áp dụng khi container web khởi động.

**Không chạy `docker compose down -v`**, vì thao tác đó có thể xóa toàn bộ volume database của đồ án.

## 4. Kiểm tra PostgreSQL và các bài test

```powershell
docker compose exec web python manage.py showmigrations clinic
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py check
docker compose exec web python manage.py test clinic
```

Kết quả mong đợi:

```text
clinic
 [X] 0001_initial
 [X] 0002_doctor_appointment
```

- `makemigrations --check --dry-run`: `No changes detected`.
- `check`: `System check identified no issues`.
- `test clinic`: có **23 bài kiểm thử** và dòng cuối `OK`.

Để xác nhận bệnh nhân Bước 2 còn nguyên, bạn có thể kiểm tra **chỉ mã bệnh nhân** (không in dữ liệu cá nhân):

```powershell
docker compose exec web python manage.py shell -c "from clinic.models import Patient; print(list(Patient.objects.values_list('patient_code', flat=True)))"
```

Nếu bạn đã tạo `BN001` ở Bước 2 và chưa xóa, mã này phải còn trong kết quả.

## 5. Kiểm tra trên trình duyệt

Đăng nhập tài khoản superuser đã tạo từ trước nếu được hỏi.

### Quản lý bác sĩ

- Mở <http://localhost:8000/doctors/>.
- Chọn `+ Thêm bác sĩ`.
- Nhập dữ liệu giả lập: mã `BS001`, tên `Bác sĩ Nguyễn Bình`, chuyên khoa `Nội tổng quát`, đánh dấu `Đang làm việc`.
- Lưu và kiểm tra mã `BS001` xuất hiện trong danh sách.
- Tìm `Nội` hoặc `BS001`.
- Nhấn `Sửa` để đổi số điện thoại hoặc chuyển trạng thái ngừng làm việc (không xóa lịch sử).

### Quản lý lịch hẹn

- Trước tiên cần có **ít nhất một bệnh nhân** và **một bác sĩ đang làm việc**.
- Mở <http://localhost:8000/appointments/>.
- Nhấn `+ Đặt lịch khám`.
- Chọn bệnh nhân `BN001` nếu bạn đã tạo, chọn bác sĩ `BS001`.
- Chọn **ngày giờ trong tương lai** theo giờ Việt Nam, chọn trạng thái `Chờ khám`, nhập lý do giả lập.
- Lưu và kiểm tra lịch xuất hiện trong danh sách.
- Thử đặt một lịch thứ hai với **cùng bác sĩ và cùng ngày giờ**: hệ thống phải báo trùng lịch.
- Thử tạo lịch ở giờ khác: phải lưu được.
- Hủy lịch qua nút `Hủy lịch`, xác nhận và kiểm tra trạng thái `Đã hủy`.
- Sau khi hủy, giờ đó có thể được đặt lại.

Bạn cũng có thể kiểm tra bảng Bác sĩ và Lịch hẹn tại <http://localhost:8000/admin/>.

## 6. Vai trò của các file

| File | Phần việc |
| --- | --- |
| `clinic/models.py` | Thêm model `Doctor`, `Appointment`; giữ model `Patient`; quan hệ ForeignKey và ràng buộc chống trùng giờ |
| `clinic/migrations/0002_doctor_appointment.py` | Tạo thêm hai bảng, không xóa bảng bệnh nhân |
| `clinic/forms.py` | Form bác sĩ/lịch hẹn; thời gian theo `datetime-local`; bác sĩ đang làm việc |
| `clinic/views.py` | Chức năng CRUD, tìm kiếm, lọc, hủy lịch; bảo vệ bệnh nhân có lịch hẹn |
| `clinic/urls.py` | Các đường dẫn `/doctors/` và `/appointments/` |
| `clinic/admin.py` | Đăng ký hai bảng trong Django Admin |
| `clinic/tests.py` | Bộ kiểm thử từ Bước 1 đến Bước 3, tổng 23 bài |
| `templates/clinic/doctor_*.html` | Trang danh sách và form bác sĩ |
| `templates/clinic/appointment_*.html` | Trang danh sách, form, xác nhận hủy |
| `templates/clinic/base.html` | Thêm điều hướng Bác sĩ và Lịch khám |
| `templates/clinic/home.html` | Liên kết nhanh từ trang chủ |
| `clinic/static/clinic/styles.css` | Kiểu hiển thị trạng thái, bảng, form |

## 7. Nếu gặp lỗi

```powershell
docker compose logs --tail=100 web
docker compose logs --tail=100 db
```

Gửi phần traceback liên quan đến lỗi, không gửi `.env`, mật khẩu hay dữ liệu bệnh nhân thật.

Đây là dự án thực hành, chưa phải hệ thống phù hợp để vận hành với hồ sơ y tế thực tế. Những phần phân quyền lễ tân/bác sĩ, quản lý ca trực, lịch sử thao tác, sao lưu, HTTPS, giám sát sẽ được phát triển theo báo cáo ở các bước tiếp theo.
