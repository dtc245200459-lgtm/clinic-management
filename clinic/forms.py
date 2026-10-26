from django import forms
from django.utils import timezone

from django.db.models import Q

from .models import (
    Appointment, Doctor, MedicalRecord, Medicine, Patient, Prescription, PrescriptionItem,
)


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["patient_code", "full_name", "date_of_birth", "gender", "phone", "address"]
        widgets = {
            "patient_code": forms.TextInput(attrs={"placeholder": "VD: BN001"}),
            "full_name": forms.TextInput(attrs={"placeholder": "Nguyễn Văn An"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "phone": forms.TextInput(attrs={"placeholder": "Số điện thoại liên hệ"}),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": "Địa chỉ liên hệ"}),
        }

    def clean_patient_code(self):
        return self.cleaned_data["patient_code"].strip().upper()

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get("date_of_birth")
        if date_of_birth and date_of_birth > timezone.localdate():
            raise forms.ValidationError("Ngày sinh không được nằm trong tương lai.")
        return date_of_birth


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["doctor_code", "full_name", "specialty", "phone", "is_active"]
        widgets = {
            "doctor_code": forms.TextInput(attrs={"placeholder": "VD: BS001"}),
            "full_name": forms.TextInput(attrs={"placeholder": "Nguyễn Văn Bình"}),
            "specialty": forms.TextInput(attrs={"placeholder": "VD: Nội tổng quát"}),
        }

    def clean_doctor_code(self):
        return self.cleaned_data["doctor_code"].strip().upper()


class AppointmentForm(forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        label="Ngày giờ khám",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )

    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "scheduled_at", "status", "reason"]
        widgets = {"reason": forms.Textarea(attrs={"rows": 3, "placeholder": "Lý do đến khám (demo)"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_doctor_id = self.instance.doctor_id if self.instance.pk else None
        doctors = Q(is_active=True)
        if current_doctor_id:
            doctors |= Q(pk=current_doctor_id)
        self.fields["doctor"].queryset = Doctor.objects.filter(doctors)

    def clean(self):
        cleaned_data = super().clean()
        if (self.instance.pk and self.has_changed()
                and MedicalRecord.objects.filter(appointment_id=self.instance.pk).exists()):
            raise forms.ValidationError(
                "Lịch hẹn đã có hồ sơ khám, không thể chỉnh sửa thông tin hay trạng thái."
            )
        return cleaned_data


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ["appointment", "examined_at", "symptoms", "diagnosis", "treatment_plan"]
        widgets = {
            "examined_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "symptoms": forms.Textarea(attrs={"rows": 4, "placeholder": "Ghi nhận do bác sĩ nhập (dữ liệu giả lập)"}),
            "diagnosis": forms.Textarea(attrs={"rows": 4}),
            "treatment_plan": forms.Textarea(attrs={"rows": 3}),
        }

    examined_at = forms.DateTimeField(
        label="Thời điểm khám",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop("doctor", None)
        super().__init__(*args, **kwargs)
        available = Appointment.objects.exclude(status=Appointment.Status.CANCELLED).filter(
            medical_record__isnull=True
        )
        if self.instance.pk:
            available = Appointment.objects.filter(
                Q(pk=self.instance.appointment_id) | Q(pk__in=available.values("pk"))
            )
            self.fields["appointment"].disabled = True
        if doctor is not None:
            available = available.filter(doctor=doctor)
        self.fields["appointment"].queryset = available.select_related("patient", "doctor")


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["name", "unit", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 4})}


class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ["medicine", "quantity", "dosage", "frequency", "instructions"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1}),
            "dosage": forms.TextInput(attrs={"placeholder": "Bác sĩ tự nhập, không có gợi ý liều"}),
            "instructions": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        medicines = Q(is_active=True)
        if self.instance.pk:
            medicines |= Q(pk=self.instance.medicine_id)
        self.fields["medicine"].queryset = Medicine.objects.filter(medicines)
