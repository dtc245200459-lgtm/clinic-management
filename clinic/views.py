from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError, connection, transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AppointmentForm, DoctorForm, MedicalRecordForm, MedicineForm, PatientForm,
    PrescriptionForm, PrescriptionItemForm,
)
from .models import Appointment, Doctor, MedicalRecord, Medicine, Patient, Prescription, PrescriptionItem
from .permissions import ROLE_ADMIN, ROLE_DOCTOR, ROLE_RECEPTION, role_required, user_has_role


def _doctor_owned(request, queryset, relation="doctor"):
    """Lọc dữ liệu cho bác sĩ; quản trị viên xem tất cả."""
    if user_has_role(request.user, ROLE_ADMIN):
        return queryset
    return queryset.filter(**{f"{relation}__user": request.user})


def database_ready():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone()[0] == 1
    except DatabaseError:
        return False


def home(request):
    return render(request, "clinic/home.html", {"db_ready": database_ready()})


def health(request):
    is_ready = database_ready()
    return JsonResponse(
        {"status": "ok" if is_ready else "database_unavailable"},
        status=200 if is_ready else 503,
    )


@role_required(ROLE_ADMIN, ROLE_RECEPTION)
def patient_list(request):
    query = request.GET.get("q", "").strip()
    patients = Patient.objects.all()
    if query:
        patients = patients.filter(
            Q(patient_code__icontains=query)
            | Q(full_name__icontains=query)
            | Q(phone__icontains=query)
        )
    page_obj = Paginator(patients, 10).get_page(request.GET.get("page"))
    return render(request, "clinic/patient_list.html", {"page_obj": page_obj, "query": query})


@role_required(ROLE_ADMIN, ROLE_RECEPTION)
def patient_create(request):
    form = PatientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã thêm bệnh nhân thành công.")
        return redirect("patient_list")
    return render(request, "clinic/patient_form.html", {"form": form, "page_title": "Thêm bệnh nhân"})


@role_required(ROLE_ADMIN, ROLE_RECEPTION)
def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = PatientForm(request.POST or None, instance=patient)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật thông tin bệnh nhân.")
        return redirect("patient_list")
    return render(request, "clinic/patient_form.html", {"form": form, "page_title": "Sửa bệnh nhân"})


@role_required(ROLE_ADMIN, ROLE_RECEPTION)
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        try:
            patient.delete()
            messages.success(request, "Đã xóa bệnh nhân trong dữ liệu demo.")
        except ProtectedError:
            messages.error(request, "Không thể xóa bệnh nhân đã có lịch hẹn. Cần giữ lịch sử khám.")
        return redirect("patient_list")
    return render(request, "clinic/patient_confirm_delete.html", {"patient": patient})


@role_required(ROLE_ADMIN, ROLE_RECEPTION, ROLE_DOCTOR)
def doctor_list(request):
    query = request.GET.get("q", "").strip()
    doctors = Doctor.objects.all()
    if query:
        doctors = doctors.filter(
            Q(doctor_code__icontains=query)
            | Q(full_name__icontains=query)
            | Q(specialty__icontains=query)
        )
    page_obj = Paginator(doctors, 10).get_page(request.GET.get("page"))
    return render(request, "clinic/doctor_list.html", {"page_obj": page_obj, "query": query})


@role_required(ROLE_ADMIN)
def doctor_create(request):
    form = DoctorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã thêm bác sĩ thành công.")
        return redirect("doctor_list")
    return render(request, "clinic/doctor_form.html", {"form": form, "page_title": "Thêm bác sĩ"})


@role_required(ROLE_ADMIN)
def doctor_update(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    form = DoctorForm(request.POST or None, instance=doctor)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật thông tin bác sĩ.")
        return redirect("doctor_list")
    return render(request, "clinic/doctor_form.html", {"form": form, "page_title": "Sửa bác sĩ"})


@role_required(ROLE_ADMIN, ROLE_RECEPTION, ROLE_DOCTOR)
def appointment_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    appointments = _doctor_owned(
        request, Appointment.objects.select_related("patient", "doctor")
    ) if not user_has_role(request.user, ROLE_RECEPTION) else Appointment.objects.select_related("patient", "doctor")
    if query:
        appointments = appointments.filter(
            Q(patient__patient_code__icontains=query)
            | Q(patient__full_name__icontains=query)
            | Q(doctor__full_name__icontains=query)
        )
    valid_statuses = {value for value, _label in Appointment.Status.choices}
    if status in valid_statuses:
        appointments = appointments.filter(status=status)
    else:
        status = ""
    page_obj = Paginator(appointments, 10).get_page(request.GET.get("page"))
    return render(request, "clinic/appointment_list.html", {
        "page_obj": page_obj, "query": query, "status": status,
        "status_choices": Appointment.Status.choices,
    })


@role_required(ROLE_ADMIN, ROLE_RECEPTION)
def appointment_create(request):
    form = AppointmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã đặt lịch hẹn thành công.")
        return redirect("appointment_list")
    return render(request, "clinic/appointment_form.html", {"form": form, "page_title": "Đặt lịch khám"})


@role_required(ROLE_ADMIN, ROLE_RECEPTION)
def appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if MedicalRecord.objects.filter(appointment=appointment).exists():
        messages.error(request, "Lịch này đã có hồ sơ khám; không thể sửa thông tin lịch hẹn.")
        return redirect("appointment_list")
    form = AppointmentForm(request.POST or None, instance=appointment)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật lịch hẹn.")
        return redirect("appointment_list")
    return render(request, "clinic/appointment_form.html", {"form": form, "page_title": "Sửa lịch hẹn"})


@role_required(ROLE_ADMIN, ROLE_RECEPTION)
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.status == Appointment.Status.COMPLETED:
        messages.error(request, "Lượt khám đã hoàn thành, không thể hủy.")
        return redirect("appointment_list")
    if request.method == "POST":
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status"])
        messages.success(request, "Đã hủy lịch hẹn nhưng vẫn giữ lịch sử.")
        return redirect("appointment_list")
    return render(request, "clinic/appointment_confirm_cancel.html", {"appointment": appointment})


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def medical_record_list(request):
    query = request.GET.get("q", "").strip()
    records = MedicalRecord.objects.select_related("appointment__patient", "appointment__doctor")
    records = _doctor_owned(request, records, "appointment__doctor")
    if query:
        records = records.filter(
            Q(appointment__patient__patient_code__icontains=query)
            | Q(appointment__patient__full_name__icontains=query)
            | Q(appointment__doctor__full_name__icontains=query)
        )
    page_obj = Paginator(records, 10).get_page(request.GET.get("page"))
    return render(request, "clinic/medical_record_list.html", {"page_obj": page_obj, "query": query})


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def medical_record_create(request):
    doctor = None
    if not user_has_role(request.user, ROLE_ADMIN):
        doctor = Doctor.objects.filter(user=request.user).first()
        if doctor is None:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Tài khoản bác sĩ chưa được liên kết với hồ sơ bác sĩ.")
    form = MedicalRecordForm(request.POST or None, doctor=doctor)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            appointment = Appointment.objects.select_for_update().get(pk=form.cleaned_data["appointment"].pk)
            if appointment.status == Appointment.Status.CANCELLED:
                form.add_error("appointment", "Lịch đã hủy, vui lòng chọn lịch khác.")
            elif MedicalRecord.objects.filter(appointment=appointment).exists():
                form.add_error("appointment", "Lịch đã có hồ sơ khám.")
            else:
                record = form.save()
                appointment.status = Appointment.Status.COMPLETED
                appointment.save(update_fields=["status"])
                messages.success(request, "Đã lưu hồ sơ khám và chuyển lịch hẹn sang 'Đã khám'.")
                return redirect("medical_record_detail", pk=record.pk)
    return render(request, "clinic/medical_record_form.html", {
        "form": form, "page_title": "Tạo hồ sơ khám", "is_edit": False,
    })


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def medical_record_detail(request, pk):
    record = get_object_or_404(
        _doctor_owned(
            request, MedicalRecord.objects.select_related("appointment__patient", "appointment__doctor"),
            "appointment__doctor",
        ), pk=pk
    )
    prescription = Prescription.objects.filter(record=record).first()
    return render(request, "clinic/medical_record_detail.html", {
        "record": record, "prescription": prescription,
    })


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def medical_record_update(request, pk):
    record = get_object_or_404(
        _doctor_owned(request, MedicalRecord.objects.all(), "appointment__doctor"), pk=pk
    )
    doctor = record.appointment.doctor if not user_has_role(request.user, ROLE_ADMIN) else None
    form = MedicalRecordForm(request.POST or None, instance=record, doctor=doctor)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật nội dung hồ sơ khám.")
        return redirect("medical_record_detail", pk=record.pk)
    return render(request, "clinic/medical_record_form.html", {
        "form": form, "page_title": "Sửa hồ sơ khám", "is_edit": True,
    })


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def medicine_list(request):
    query = request.GET.get("q", "").strip()
    medicines = Medicine.objects.all()
    if query:
        medicines = medicines.filter(Q(name__icontains=query) | Q(unit__icontains=query))
    page_obj = Paginator(medicines, 10).get_page(request.GET.get("page"))
    return render(request, "clinic/medicine_list.html", {"page_obj": page_obj, "query": query})


@role_required(ROLE_ADMIN)
def medicine_create(request):
    form = MedicineForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã thêm thuốc vào danh mục demo.")
        return redirect("medicine_list")
    return render(request, "clinic/medicine_form.html", {"form": form, "page_title": "Thêm thuốc"})


@role_required(ROLE_ADMIN)
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    form = MedicineForm(request.POST or None, instance=medicine)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật thuốc.")
        return redirect("medicine_list")
    return render(request, "clinic/medicine_form.html", {"form": form, "page_title": "Sửa thuốc"})


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def prescription_create(request, record_pk):
    record = get_object_or_404(
        _doctor_owned(request, MedicalRecord.objects.all(), "appointment__doctor"), pk=record_pk
    )
    prescription = Prescription.objects.filter(record=record).first()
    if prescription:
        messages.info(request, "Hồ sơ khám này đã có đơn thuốc.")
        return redirect("prescription_detail", pk=prescription.pk)
    form = PrescriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        prescription = form.save(commit=False)
        prescription.record = record
        prescription.save()
        messages.success(request, "Đã tạo đơn thuốc. Bây giờ hãy thêm từng dòng thuốc.")
        return redirect("prescription_detail", pk=prescription.pk)
    return render(request, "clinic/prescription_form.html", {
        "record": record, "form": form, "page_title": "Tạo đơn thuốc",
    })


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def prescription_update(request, pk):
    prescription = get_object_or_404(
        _doctor_owned(request, Prescription.objects.all(), "record__appointment__doctor"), pk=pk
    )
    form = PrescriptionForm(request.POST or None, instance=prescription)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật ghi chú đơn thuốc.")
        return redirect("prescription_detail", pk=prescription.pk)
    return render(request, "clinic/prescription_form.html", {
        "record": prescription.record, "form": form,
        "page_title": "Sửa ghi chú đơn thuốc",
    })


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def prescription_detail(request, pk):
    prescription = get_object_or_404(
        _doctor_owned(
            request, Prescription.objects.select_related(
                "record__appointment__patient", "record__appointment__doctor"
            ), "record__appointment__doctor",
        ), pk=pk
    )
    items = prescription.items.select_related("medicine")
    return render(request, "clinic/prescription_detail.html", {
        "prescription": prescription, "items": items,
    })


def _prescription_item_form(request, prescription, item=None):
    form = PrescriptionItemForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        medicine = form.cleaned_data["medicine"]
        duplicates = prescription.items.filter(medicine=medicine)
        if item:
            duplicates = duplicates.exclude(pk=item.pk)
        if duplicates.exists():
            form.add_error("medicine", "Thuốc này đã có trong đơn; hãy sửa dòng hiện tại.")
        else:
            saved_item = form.save(commit=False)
            saved_item.prescription = prescription
            saved_item.save()
            messages.success(request, "Đã lưu dòng thuốc.")
            return redirect("prescription_detail", pk=prescription.pk)
    return render(request, "clinic/prescription_item_form.html", {
        "form": form, "prescription": prescription,
        "page_title": "Sửa dòng thuốc" if item else "Thêm thuốc vào đơn",
    })


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def prescription_item_create(request, pk):
    prescription = get_object_or_404(
        _doctor_owned(request, Prescription.objects.all(), "record__appointment__doctor"), pk=pk
    )
    return _prescription_item_form(request, prescription)


@role_required(ROLE_ADMIN, ROLE_DOCTOR)
def prescription_item_update(request, pk, item_pk):
    prescription = get_object_or_404(
        _doctor_owned(request, Prescription.objects.all(), "record__appointment__doctor"), pk=pk
    )
    item = get_object_or_404(PrescriptionItem, pk=item_pk, prescription=prescription)
    return _prescription_item_form(request, prescription, item)
