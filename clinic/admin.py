from django.contrib import admin

from .forms import AppointmentForm
from .models import Appointment, Doctor, MedicalRecord, Medicine, Patient, Prescription, PrescriptionItem


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_code", "full_name", "date_of_birth", "gender", "phone", "created_at")
    search_fields = ("patient_code", "full_name", "phone")
    list_filter = ("gender",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("doctor_code", "full_name", "specialty", "user", "phone", "is_active")
    search_fields = ("doctor_code", "full_name", "specialty")
    list_filter = ("is_active", "specialty")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentForm
    list_display = ("patient", "doctor", "scheduled_at", "status")
    search_fields = ("patient__patient_code", "patient__full_name", "doctor__full_name")
    list_filter = ("status", "doctor")


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "examined_at")
    search_fields = ("appointment__patient__patient_code", "appointment__doctor__full_name")
    readonly_fields = ("created_at",)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 0


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "record", "created_at")
    inlines = [PrescriptionItemInline]


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ("prescription", "medicine", "quantity", "dosage")
