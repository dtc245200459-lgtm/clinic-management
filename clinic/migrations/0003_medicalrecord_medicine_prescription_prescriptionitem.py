import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clinic", "0002_doctor_appointment")]

    operations = [
        migrations.CreateModel(
            name="MedicalRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symptoms", models.TextField(verbose_name="Triệu chứng ghi nhận")),
                ("diagnosis", models.TextField(verbose_name="Chẩn đoán do bác sĩ nhập")),
                ("treatment_plan", models.TextField(blank=True, verbose_name="Hướng xử trí")),
                ("examined_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Thời điểm khám")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")),
                ("appointment", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="medical_record", to="clinic.appointment", verbose_name="Lịch hẹn")),
            ],
            options={
                "verbose_name": "Hồ sơ khám", "verbose_name_plural": "Hồ sơ khám",
                "ordering": ["-examined_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="Medicine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, unique=True, verbose_name="Tên thuốc")),
                ("unit", models.CharField(max_length=30, verbose_name="Đơn vị")),
                ("description", models.TextField(blank=True, verbose_name="Mô tả")),
                ("is_active", models.BooleanField(default=True, verbose_name="Đang sử dụng")),
            ],
            options={
                "verbose_name": "Thuốc", "verbose_name_plural": "Thuốc",
                "ordering": ["name", "id"],
            },
        ),
        migrations.CreateModel(
            name="Prescription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notes", models.TextField(blank=True, verbose_name="Ghi chú đơn thuốc")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")),
                ("record", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="prescription", to="clinic.medicalrecord", verbose_name="Hồ sơ khám")),
            ],
            options={"verbose_name": "Đơn thuốc", "verbose_name_plural": "Đơn thuốc"},
        ),
        migrations.CreateModel(
            name="PrescriptionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="Số lượng")),
                ("dosage", models.CharField(max_length=120, verbose_name="Liều dùng do bác sĩ nhập")),
                ("frequency", models.CharField(blank=True, max_length=120, verbose_name="Tần suất")),
                ("instructions", models.TextField(blank=True, verbose_name="Hướng dẫn")),
                ("medicine", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prescription_items", to="clinic.medicine", verbose_name="Thuốc")),
                ("prescription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="clinic.prescription", verbose_name="Đơn thuốc")),
            ],
            options={
                "verbose_name": "Chi tiết đơn thuốc", "verbose_name_plural": "Chi tiết đơn thuốc",
                "ordering": ["id"],
                "constraints": [models.UniqueConstraint(fields=("prescription", "medicine"), name="unique_medicine_per_prescription")],
            },
        ),
    ]
