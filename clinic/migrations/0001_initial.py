# Initial schema for Patient.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Patient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("patient_code", models.CharField(max_length=20, unique=True, verbose_name="Mã bệnh nhân")),
                ("full_name", models.CharField(max_length=150, verbose_name="Họ và tên")),
                ("date_of_birth", models.DateField(blank=True, null=True, verbose_name="Ngày sinh")),
                ("gender", models.CharField(blank=True, choices=[("M", "Nam"), ("F", "Nữ"), ("O", "Khác")], max_length=1, verbose_name="Giới tính")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="Số điện thoại")),
                ("address", models.TextField(blank=True, verbose_name="Địa chỉ")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Cập nhật lúc")),
            ],
            options={
                "verbose_name": "Bệnh nhân",
                "verbose_name_plural": "Bệnh nhân",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
