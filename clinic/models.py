from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Nam"
        FEMALE = "F", "Nữ"
        OTHER = "O", "Khác"

    patient_code = models.CharField("Mã bệnh nhân", max_length=20, unique=True)
    full_name = models.CharField("Họ và tên", max_length=150)
    date_of_birth = models.DateField("Ngày sinh", null=True, blank=True)
    gender = models.CharField("Giới tính", max_length=1, choices=Gender.choices, blank=True)
    phone = models.CharField("Số điện thoại", max_length=20, blank=True)
    address = models.TextField("Địa chỉ", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Cập nhật lúc", auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Bệnh nhân"
        verbose_name_plural = "Bệnh nhân"

    def __str__(self):
        return f"{self.patient_code} - {self.full_name}"


class Doctor(models.Model):
    doctor_code = models.CharField("Mã bác sĩ", max_length=20, unique=True)
    full_name = models.CharField("Họ và tên", max_length=150)
    specialty = models.CharField("Chuyên khoa", max_length=100)
    phone = models.CharField("Số điện thoại", max_length=20, blank=True)
    is_active = models.BooleanField("Đang làm việc", default=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doctor_profile",
        verbose_name="Tài khoản đăng nhập",
        help_text="Chọn tài khoản thuộc nhóm Bác sĩ; mỗi tài khoản chỉ gắn với một bác sĩ.",
    )

    class Meta:
        ordering = ["full_name", "id"]
        verbose_name = "Bác sĩ"
        verbose_name_plural = "Bác sĩ"

    def __str__(self):
        return f"{self.doctor_code} - {self.full_name} ({self.specialty})"


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Chờ khám"
        COMPLETED = "completed", "Đã khám"
        CANCELLED = "cancelled", "Đã hủy"

    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="appointments", verbose_name="Bệnh nhân"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name="appointments", verbose_name="Bác sĩ"
    )
    scheduled_at = models.DateTimeField("Ngày giờ khám")
    status = models.CharField(
        "Trạng thái", max_length=10, choices=Status.choices, default=Status.SCHEDULED
    )
    reason = models.TextField("Lý do khám", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_at", "-id"]
        verbose_name = "Lịch hẹn"
        verbose_name_plural = "Lịch hẹn"
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "scheduled_at"],
                condition=~models.Q(status="cancelled"),
                name="unique_active_appointment_per_doctor_slot",
            )
        ]

    def clean(self):
        super().clean()
        if self._state.adding and self.status == self.Status.SCHEDULED:
            if self.scheduled_at and self.scheduled_at < timezone.now():
                raise ValidationError({"scheduled_at": "Lịch hẹn mới phải ở thời điểm tương lai."})
        if self._state.adding and self.doctor_id and not self.doctor.is_active:
            raise ValidationError({"doctor": "Không thể đặt lịch mới với bác sĩ đã ngừng làm việc."})
        if self.doctor_id and self.scheduled_at and self.status != self.Status.CANCELLED:
            conflict = Appointment.objects.filter(
                doctor_id=self.doctor_id, scheduled_at=self.scheduled_at
            ).exclude(status=self.Status.CANCELLED).exclude(pk=self.pk)
            if conflict.exists():
                raise ValidationError({"scheduled_at": "Bác sĩ đã có lịch khám vào thời điểm này."})

    def __str__(self):
        return f"{self.patient.patient_code} - {self.doctor.doctor_code} - {self.scheduled_at:%d/%m/%Y %H:%M}"


class MedicalRecord(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.PROTECT, related_name="medical_record", verbose_name="Lịch hẹn"
    )
    symptoms = models.TextField("Triệu chứng ghi nhận")
    diagnosis = models.TextField("Chẩn đoán do bác sĩ nhập")
    treatment_plan = models.TextField("Hướng xử trí", blank=True)
    examined_at = models.DateTimeField("Thời điểm khám", default=timezone.now)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        ordering = ["-examined_at", "-id"]
        verbose_name = "Hồ sơ khám"
        verbose_name_plural = "Hồ sơ khám"

    def clean(self):
        super().clean()
        if self.appointment_id and self.appointment.status == Appointment.Status.CANCELLED:
            raise ValidationError({"appointment": "Không thể tạo hồ sơ khám cho lịch đã hủy."})

    def __str__(self):
        return f"Hồ sơ #{self.pk or 'mới'} - {self.appointment.patient.patient_code}"


class Medicine(models.Model):
    name = models.CharField("Tên thuốc", max_length=150, unique=True)
    unit = models.CharField("Đơn vị", max_length=30)
    description = models.TextField("Mô tả", blank=True)
    is_active = models.BooleanField("Đang sử dụng", default=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Thuốc"
        verbose_name_plural = "Thuốc"

    def __str__(self):
        return f"{self.name} ({self.unit})"


class Prescription(models.Model):
    record = models.OneToOneField(
        MedicalRecord, on_delete=models.PROTECT, related_name="prescription", verbose_name="Hồ sơ khám"
    )
    notes = models.TextField("Ghi chú đơn thuốc", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        verbose_name = "Đơn thuốc"
        verbose_name_plural = "Đơn thuốc"

    def __str__(self):
        return f"Đơn thuốc #{self.pk or 'mới'} - hồ sơ #{self.record_id}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="items", verbose_name="Đơn thuốc"
    )
    medicine = models.ForeignKey(
        Medicine, on_delete=models.PROTECT, related_name="prescription_items", verbose_name="Thuốc"
    )
    quantity = models.PositiveIntegerField("Số lượng", validators=[MinValueValidator(1)])
    dosage = models.CharField("Liều dùng do bác sĩ nhập", max_length=120)
    frequency = models.CharField("Tần suất", max_length=120, blank=True)
    instructions = models.TextField("Hướng dẫn", blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Chi tiết đơn thuốc"
        verbose_name_plural = "Chi tiết đơn thuốc"
        constraints = [
            models.UniqueConstraint(
                fields=["prescription", "medicine"], name="unique_medicine_per_prescription"
            )
        ]

    def __str__(self):
        return f"{self.medicine.name} × {self.quantity}"
