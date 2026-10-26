import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clinic", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Doctor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("doctor_code", models.CharField(max_length=20, unique=True, verbose_name="Mã bác sĩ")),
                ("full_name", models.CharField(max_length=150, verbose_name="Họ và tên")),
                ("specialty", models.CharField(max_length=100, verbose_name="Chuyên khoa")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="Số điện thoại")),
                ("is_active", models.BooleanField(default=True, verbose_name="Đang làm việc")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")),
            ],
            options={
                "verbose_name": "Bác sĩ",
                "verbose_name_plural": "Bác sĩ",
                "ordering": ["full_name", "id"],
            },
        ),
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scheduled_at", models.DateTimeField(verbose_name="Ngày giờ khám")),
                ("status", models.CharField(choices=[("scheduled", "Chờ khám"), ("completed", "Đã khám"), ("cancelled", "Đã hủy")], default="scheduled", max_length=10, verbose_name="Trạng thái")),
                ("reason", models.TextField(blank=True, verbose_name="Lý do khám")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")),
                ("doctor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="appointments", to="clinic.doctor", verbose_name="Bác sĩ")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="appointments", to="clinic.patient", verbose_name="Bệnh nhân")),
            ],
            options={
                "verbose_name": "Lịch hẹn",
                "verbose_name_plural": "Lịch hẹn",
                "ordering": ["-scheduled_at", "-id"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("doctor", "scheduled_at"),
                        condition=~models.Q(status="cancelled"),
                        name="unique_active_appointment_per_doctor_slot",
                    )
                ],
            },
        ),
    ]
