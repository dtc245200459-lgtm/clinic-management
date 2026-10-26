from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Appointment, Doctor, MedicalRecord, Medicine, Patient, Prescription, PrescriptionItem


class ClinicStarterTests(TestCase):
    def test_homepage_loads_and_database_responds(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["db_ready"])

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class PatientTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="admin_test", email="admin@example.test", password="safe_test_password_2026"
        )
        cls.patient = Patient.objects.create(patient_code="BN001", full_name="Nguyễn Văn An", phone="0901234567")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_patient_list(self):
        response = self.client.get(reverse("patient_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BN001")

    def test_search_by_patient_code(self):
        response = self.client.get(reverse("patient_list"), {"q": "BN001"})
        self.assertContains(response, "Nguyễn Văn An")

    def test_create_patient(self):
        response = self.client.post(reverse("patient_create"), {
            "patient_code": "bn002", "full_name": "Trần Thị Bình", "phone": "0912345678"
        })
        self.assertRedirects(response, reverse("patient_list"))
        self.assertTrue(Patient.objects.filter(patient_code="BN002").exists())

    def test_update_patient(self):
        response = self.client.post(reverse("patient_update", args=[self.patient.pk]), {
            "patient_code": "BN001", "full_name": "Nguyễn Văn An Mới", "phone": "0901234567"
        })
        self.assertRedirects(response, reverse("patient_list"))
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.full_name, "Nguyễn Văn An Mới")

    def test_delete_requires_confirmation_post(self):
        url = reverse("patient_delete", args=[self.patient.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Patient.objects.filter(pk=self.patient.pk).exists())
        self.assertRedirects(self.client.post(url), reverse("patient_list"))
        self.assertFalse(Patient.objects.filter(pk=self.patient.pk).exists())

    def test_duplicate_patient_code_rejected(self):
        response = self.client.post(reverse("patient_create"), {
            "patient_code": "BN001", "full_name": "Bệnh nhân trùng mã"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertTrue(response.context["form"].errors)

    def test_future_birth_date_rejected(self):
        response = self.client.post(reverse("patient_create"), {
            "patient_code": "BN003",
            "full_name": "Bệnh nhân giả lập",
            "date_of_birth": (timezone.localdate() + timedelta(days=1)).isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Patient.objects.filter(patient_code="BN003").exists())

    def test_anonymous_user_cannot_list_patients(self):
        self.client.logout()
        response = self.client.get(reverse("patient_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class DoctorAppointmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="admin_schedule", email="schedule@example.test", password="safe_test_password_2026"
        )
        cls.patient = Patient.objects.create(patient_code="BN101", full_name="Bệnh nhân Thử Nghiệm")
        cls.doctor = Doctor.objects.create(
            doctor_code="BS001", full_name="Bác sĩ Nguyễn Bình", specialty="Nội tổng quát"
        )
        cls.doctor_other = Doctor.objects.create(
            doctor_code="BS002", full_name="Bác sĩ Trần Minh", specialty="Nhi khoa"
        )
        cls.slot = (timezone.now() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)

    def setUp(self):
        self.client.force_login(self.admin)

    def appointment_post_data(self, doctor=None, status="scheduled", scheduled_at=None):
        return {
            "patient": self.patient.pk,
            "doctor": (doctor or self.doctor).pk,
            "scheduled_at": timezone.localtime(scheduled_at or self.slot).strftime("%Y-%m-%dT%H:%M"),
            "status": status,
            "reason": "Khám giả lập",
        }

    def test_doctor_create_normalizes_code(self):
        response = self.client.post(reverse("doctor_create"), {
            "doctor_code": "bs003", "full_name": "Bác sĩ Lê Hà",
            "specialty": "Da liễu", "is_active": "on",
        })
        self.assertRedirects(response, reverse("doctor_list"))
        self.assertTrue(Doctor.objects.filter(doctor_code="BS003", is_active=True).exists())

    def test_doctor_search_and_update(self):
        self.assertContains(self.client.get(reverse("doctor_list"), {"q": "Nội"}), "BS001")
        response = self.client.post(reverse("doctor_update", args=[self.doctor.pk]), {
            "doctor_code": "BS001", "full_name": "Bác sĩ Nguyễn Bình",
            "specialty": "Nội tổng quát", "phone": "0900000000",
        })
        self.assertRedirects(response, reverse("doctor_list"))
        self.doctor.refresh_from_db()
        self.assertFalse(self.doctor.is_active)

    def test_appointment_create(self):
        response = self.client.post(reverse("appointment_create"), self.appointment_post_data())
        self.assertRedirects(response, reverse("appointment_list"))
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(Appointment.objects.get().patient, self.patient)

    def test_doctor_cannot_have_two_active_appointments_same_time(self):
        Appointment.objects.create(patient=self.patient, doctor=self.doctor, scheduled_at=self.slot)
        response = self.client.post(reverse("appointment_create"), self.appointment_post_data())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_two_doctors_can_have_same_time_slot(self):
        Appointment.objects.create(patient=self.patient, doctor=self.doctor, scheduled_at=self.slot)
        response = self.client.post(
            reverse("appointment_create"), self.appointment_post_data(doctor=self.doctor_other)
        )
        self.assertRedirects(response, reverse("appointment_list"))
        self.assertEqual(Appointment.objects.count(), 2)

    def test_cancel_keeps_record_and_releases_slot(self):
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, scheduled_at=self.slot
        )
        url = reverse("appointment_cancel", args=[appointment.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)
        self.assertRedirects(self.client.post(url), reverse("appointment_list"))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        response = self.client.post(reverse("appointment_create"), self.appointment_post_data())
        self.assertRedirects(response, reverse("appointment_list"))
        self.assertEqual(Appointment.objects.count(), 2)

    def test_completed_appointment_cannot_be_cancelled(self):
        appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            scheduled_at=self.slot, status=Appointment.Status.COMPLETED,
        )
        self.assertRedirects(
            self.client.post(reverse("appointment_cancel", args=[appointment.pk])),
            reverse("appointment_list"),
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)

    def test_inactive_doctor_cannot_receive_new_appointment(self):
        self.doctor.is_active = False
        self.doctor.save(update_fields=["is_active"])
        response = self.client.post(reverse("appointment_create"), self.appointment_post_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_past_appointment_rejected(self):
        past = timezone.now() - timedelta(days=1)
        response = self.client.post(
            reverse("appointment_create"), self.appointment_post_data(scheduled_at=past)
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_patient_with_appointment_is_protected_from_deletion(self):
        Appointment.objects.create(patient=self.patient, doctor=self.doctor, scheduled_at=self.slot)
        self.assertRedirects(
            self.client.post(reverse("patient_delete", args=[self.patient.pk])),
            reverse("patient_list"),
        )
        self.assertTrue(Patient.objects.filter(pk=self.patient.pk).exists())

    def test_appointment_filter_by_status(self):
        Appointment.objects.create(patient=self.patient, doctor=self.doctor, scheduled_at=self.slot)
        response = self.client.get(reverse("appointment_list"), {"status": "scheduled"})
        self.assertContains(response, "Bác sĩ Nguyễn Bình")

    def test_anonymous_access_is_redirected_to_login(self):
        self.client.logout()
        for name in ("doctor_list", "appointment_list"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/", response.url)

    def test_admin_add_views_render(self):
        self.assertEqual(self.client.get(reverse("admin:clinic_doctor_add")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:clinic_appointment_add")).status_code, 200)


class MedicalRecordPrescriptionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            username="clinic_staff", email="clinic_staff@example.test", password="test_password_2026",
        )
        cls.patient = Patient.objects.create(patient_code="BN400", full_name="Bệnh nhân Mẫu")
        cls.doctor = Doctor.objects.create(
            doctor_code="BS400", full_name="Bác sĩ Mẫu", specialty="Khám giả lập",
        )
        cls.appointment = Appointment.objects.create(
            patient=cls.patient, doctor=cls.doctor,
            scheduled_at=timezone.now() + timedelta(days=3),
        )
        cls.medicine = Medicine.objects.create(name="Thuốc mẫu A", unit="viên")
        cls.medicine_other = Medicine.objects.create(name="Thuốc mẫu B", unit="hộp")

    def setUp(self):
        self.client.force_login(self.staff)

    def record_data(self, appointment=None):
        return {
            "appointment": (appointment or self.appointment).pk,
            "examined_at": timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M"),
            "symptoms": "Triệu chứng demo", "diagnosis": "Chẩn đoán demo",
            "treatment_plan": "Hướng xử trí demo",
        }

    def create_record(self):
        return MedicalRecord.objects.create(
            appointment=self.appointment, symptoms="Mô tả demo", diagnosis="Dữ liệu thử nghiệm",
        )

    def create_prescription(self):
        return Prescription.objects.create(record=self.create_record(), notes="Demo")

    def item_data(self, medicine=None, quantity="2"):
        return {
            "medicine": (medicine or self.medicine).pk, "quantity": quantity,
            "dosage": "Dữ liệu demo", "frequency": "Dữ liệu demo",
            "instructions": "Chỉ kiểm thử hệ thống",
        }

    def test_create_record_marks_appointment_completed(self):
        response = self.client.post(reverse("medical_record_create"), self.record_data())
        record = MedicalRecord.objects.get(appointment=self.appointment)
        self.assertRedirects(response, reverse("medical_record_detail", args=[record.pk]))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.COMPLETED)

    def test_cannot_create_record_on_cancelled_appointment(self):
        self.appointment.status = Appointment.Status.CANCELLED
        self.appointment.save(update_fields=["status"])
        response = self.client.post(reverse("medical_record_create"), self.record_data())
        self.assertEqual(response.status_code, 200)
        self.assertIn("appointment", response.context["form"].errors)
        self.assertEqual(MedicalRecord.objects.count(), 0)

    def test_appointment_can_only_have_one_record(self):
        self.create_record()
        response = self.client.post(reverse("medical_record_create"), self.record_data())
        self.assertEqual(response.status_code, 200)
        self.assertIn("appointment", response.context["form"].errors)
        self.assertEqual(MedicalRecord.objects.count(), 1)

    def test_record_list_search_and_detail_render(self):
        record = self.create_record()
        self.assertContains(self.client.get(reverse("medical_record_list"), {"q": "BN400"}), "BN400")
        self.assertContains(self.client.get(reverse("medical_record_detail", args=[record.pk])), "Chẩn đoán")

    def test_record_update_cannot_change_appointment(self):
        record = self.create_record()
        other_appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            scheduled_at=timezone.now() + timedelta(days=5),
        )
        data = self.record_data(appointment=other_appointment)
        data["diagnosis"] = "Nội dung được cập nhật"
        self.assertRedirects(
            self.client.post(reverse("medical_record_update", args=[record.pk]), data),
            reverse("medical_record_detail", args=[record.pk]),
        )
        record.refresh_from_db()
        self.assertEqual(record.appointment_id, self.appointment.pk)
        self.assertEqual(record.diagnosis, "Nội dung được cập nhật")

    def test_appointment_with_record_cannot_be_edited(self):
        self.create_record()
        response = self.client.get(reverse("appointment_update", args=[self.appointment.pk]))
        self.assertRedirects(response, reverse("appointment_list"))

    def test_create_and_edit_medicine(self):
        self.assertRedirects(
            self.client.post(reverse("medicine_create"), {
                "name": "Thuốc mẫu C", "unit": "lọ", "is_active": "on",
            }), reverse("medicine_list"),
        )
        medicine = Medicine.objects.get(name="Thuốc mẫu C")
        self.assertRedirects(
            self.client.post(reverse("medicine_update", args=[medicine.pk]), {
                "name": "Thuốc mẫu C", "unit": "chai", "description": "Demo",
            }), reverse("medicine_list"),
        )
        medicine.refresh_from_db()
        self.assertEqual(medicine.unit, "chai")
        self.assertFalse(medicine.is_active)

    def test_duplicate_medicine_name_rejected(self):
        response = self.client.post(reverse("medicine_create"), {
            "name": self.medicine.name, "unit": "chai", "is_active": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)

    def test_prescription_created_for_record_once(self):
        record = self.create_record()
        url = reverse("prescription_create", args=[record.pk])
        response = self.client.post(url, {"notes": "Đơn thuốc demo"})
        prescription = Prescription.objects.get(record=record)
        self.assertRedirects(response, reverse("prescription_detail", args=[prescription.pk]))
        self.assertRedirects(self.client.post(url, {"notes": "Đơn khác"}), reverse("prescription_detail", args=[prescription.pk]))
        self.assertEqual(Prescription.objects.count(), 1)

    def test_prescription_notes_can_be_updated(self):
        prescription = self.create_prescription()
        self.assertRedirects(
            self.client.post(reverse("prescription_update", args=[prescription.pk]), {"notes": "Ghi chú mới"}),
            reverse("prescription_detail", args=[prescription.pk]),
        )
        prescription.refresh_from_db()
        self.assertEqual(prescription.notes, "Ghi chú mới")

    def test_prescription_item_create_update_and_display(self):
        prescription = self.create_prescription()
        url = reverse("prescription_item_create", args=[prescription.pk])
        self.assertRedirects(
            self.client.post(url, self.item_data()), reverse("prescription_detail", args=[prescription.pk]),
        )
        item = PrescriptionItem.objects.get(prescription=prescription)
        self.assertContains(self.client.get(reverse("prescription_detail", args=[prescription.pk])), "Thuốc mẫu A")
        data = self.item_data(quantity="5")
        self.assertRedirects(
            self.client.post(reverse("prescription_item_update", args=[prescription.pk, item.pk]), data),
            reverse("prescription_detail", args=[prescription.pk]),
        )
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_cannot_add_zero_quantity(self):
        prescription = self.create_prescription()
        response = self.client.post(
            reverse("prescription_item_create", args=[prescription.pk]), self.item_data(quantity="0"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("quantity", response.context["form"].errors)
        self.assertFalse(PrescriptionItem.objects.exists())

    def test_same_medicine_cannot_be_added_twice_to_prescription(self):
        prescription = self.create_prescription()
        PrescriptionItem.objects.create(
            prescription=prescription, medicine=self.medicine, quantity=1, dosage="Demo",
        )
        response = self.client.post(
            reverse("prescription_item_create", args=[prescription.pk]), self.item_data(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("medicine", response.context["form"].errors)
        self.assertEqual(PrescriptionItem.objects.count(), 1)

    def test_cannot_select_inactive_medicine_for_new_item(self):
        prescription = self.create_prescription()
        self.medicine.is_active = False
        self.medicine.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("prescription_item_create", args=[prescription.pk]), self.item_data(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("medicine", response.context["form"].errors)

    def test_existing_inactive_medicine_can_still_be_edited(self):
        prescription = self.create_prescription()
        item = PrescriptionItem.objects.create(
            prescription=prescription, medicine=self.medicine, quantity=1, dosage="Demo",
        )
        self.medicine.is_active = False
        self.medicine.save(update_fields=["is_active"])
        self.assertRedirects(
            self.client.post(
                reverse("prescription_item_update", args=[prescription.pk, item.pk]), self.item_data(quantity="3"),
            ), reverse("prescription_detail", args=[prescription.pk]),
        )

    def test_navigation_and_new_forms_render(self):
        record = self.create_record()
        prescription = Prescription.objects.create(record=record)
        for url in (
            reverse("home"), reverse("medical_record_list"), reverse("medical_record_create"),
            reverse("medical_record_update", args=[record.pk]), reverse("medicine_list"),
            reverse("medicine_create"), reverse("prescription_detail", args=[prescription.pk]),
            reverse("prescription_update", args=[prescription.pk]),
            reverse("prescription_item_create", args=[prescription.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_anonymous_user_is_redirected(self):
        self.client.logout()
        for name in ("medical_record_list", "medical_record_create", "medicine_list", "medicine_create"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response.url)


class RoleAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(
            "admin_role", "admin_role@example.test", "safe_test_password_2026"
        )
        cls.doctor_user = User.objects.create_user(
            "doctor_role", password="safe_test_password_2026", is_staff=False,
        )
        cls.other_doctor_user = User.objects.create_user(
            "other_doctor", password="safe_test_password_2026", is_staff=False,
        )
        cls.reception_user = User.objects.create_user(
            "reception_role", password="safe_test_password_2026", is_staff=False,
        )
        cls.unassigned_user = User.objects.create_user(
            "unassigned_role", password="safe_test_password_2026", is_staff=False,
        )
        doctors_group = Group.objects.get(name="Bác sĩ")
        reception_group = Group.objects.get(name="Lễ tân")
        cls.doctor_user.groups.add(doctors_group)
        cls.other_doctor_user.groups.add(doctors_group)
        cls.reception_user.groups.add(reception_group)
        cls.patient = Patient.objects.create(patient_code="BN501", full_name="Bệnh nhân X")
        cls.patient_other = Patient.objects.create(patient_code="BN502", full_name="Bệnh nhân Y")
        cls.doctor = Doctor.objects.create(
            doctor_code="BS501", full_name="Bác sĩ X", specialty="Demo", user=cls.doctor_user,
        )
        cls.other_doctor = Doctor.objects.create(
            doctor_code="BS502", full_name="Bác sĩ Y", specialty="Demo", user=cls.other_doctor_user,
        )
        cls.appointment = Appointment.objects.create(
            patient=cls.patient, doctor=cls.doctor,
            scheduled_at=timezone.now() + timedelta(days=4),
        )
        cls.other_appointment = Appointment.objects.create(
            patient=cls.patient_other, doctor=cls.other_doctor,
            scheduled_at=timezone.now() + timedelta(days=4),
        )
        cls.record = MedicalRecord.objects.create(
            appointment=cls.appointment, symptoms="Demo", diagnosis="Demo",
        )
        cls.other_record = MedicalRecord.objects.create(
            appointment=cls.other_appointment, symptoms="Demo", diagnosis="Demo",
        )
        cls.prescription = Prescription.objects.create(record=cls.record)
        cls.other_prescription = Prescription.objects.create(record=cls.other_record)
        cls.medicine = Medicine.objects.create(name="Thuốc nhóm demo", unit="viên")

    def login_as(self, user):
        self.client.force_login(user)

    def test_groups_created_automatically_by_migration(self):
        self.assertTrue(Group.objects.filter(name="Bác sĩ").exists())
        self.assertTrue(Group.objects.filter(name="Lễ tân").exists())

    def test_login_and_logout(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        response = self.client.post(reverse("login"), {
            "username": "reception_role", "password": "safe_test_password_2026",
        })
        self.assertRedirects(response, reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_users_redirect_to_custom_login(self):
        for name in ("appointment_list", "medical_record_list", "patient_list", "medicine_list"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("login")))

    def test_unassigned_account_cannot_use_clinic(self):
        self.login_as(self.unassigned_user)
        for name in ("patient_list", "medical_record_list", "appointment_list"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_receptionist_can_manage_patients_and_appointments(self):
        self.login_as(self.reception_user)
        self.assertEqual(self.client.get(reverse("patient_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("patient_create")).status_code, 200)
        self.assertEqual(self.client.get(reverse("appointment_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("appointment_create")).status_code, 200)
        self.assertEqual(self.client.get(reverse("doctor_list")).status_code, 200)

    def test_receptionist_cannot_open_medical_records_or_prescriptions(self):
        self.login_as(self.reception_user)
        for path in (
            reverse("medical_record_list"), reverse("medical_record_detail", args=[self.record.pk]),
            reverse("medical_record_create"), reverse("prescription_detail", args=[self.prescription.pk]),
            reverse("medicine_list"), reverse("doctor_update", args=[self.doctor.pk]),
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_doctor_sees_only_their_own_appointments(self):
        self.login_as(self.doctor_user)
        response = self.client.get(reverse("appointment_list"))
        self.assertContains(response, "BN501")
        self.assertNotContains(response, "BN502")

    def test_doctor_sees_only_their_own_records(self):
        self.login_as(self.doctor_user)
        response = self.client.get(reverse("medical_record_list"))
        self.assertContains(response, "BN501")
        self.assertNotContains(response, "BN502")
        self.assertEqual(self.client.get(reverse("medical_record_detail", args=[self.record.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("medical_record_detail", args=[self.other_record.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("medical_record_update", args=[self.other_record.pk])).status_code, 404)

    def test_doctor_cannot_access_other_prescription_by_guessing_url(self):
        self.login_as(self.doctor_user)
        self.assertEqual(self.client.get(reverse("prescription_detail", args=[self.prescription.pk])).status_code, 200)
        for path in (
            reverse("prescription_detail", args=[self.other_prescription.pk]),
            reverse("prescription_update", args=[self.other_prescription.pk]),
            reverse("prescription_item_create", args=[self.other_prescription.pk]),
            reverse("prescription_create", args=[self.other_record.pk]),
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_doctor_record_form_only_offers_own_appointments(self):
        self.login_as(self.doctor_user)
        # Lịch của mình đã có hồ sơ nên thêm một lịch trống.
        free_slot = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            scheduled_at=timezone.now() + timedelta(days=9),
        )
        response = self.client.get(reverse("medical_record_create"))
        choices = response.context["form"].fields["appointment"].queryset
        self.assertIn(free_slot, choices)
        self.assertNotIn(self.other_appointment, choices)
        data = {
            "appointment": self.other_appointment.pk,
            "examined_at": timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M"),
            "symptoms": "Demo", "diagnosis": "Demo",
        }
        response = self.client.post(reverse("medical_record_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("appointment", response.context["form"].errors)

    def test_doctor_can_complete_own_record_prescription_workflow(self):
        self.login_as(self.doctor_user)
        new_appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            scheduled_at=timezone.now() + timedelta(days=10),
        )
        response = self.client.post(reverse("medical_record_create"), {
            "appointment": new_appointment.pk,
            "examined_at": timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M"),
            "symptoms": "Triệu chứng giả lập", "diagnosis": "Chẩn đoán giả lập",
        })
        record = MedicalRecord.objects.get(appointment=new_appointment)
        self.assertRedirects(response, reverse("medical_record_detail", args=[record.pk]))
        new_appointment.refresh_from_db()
        self.assertEqual(new_appointment.status, Appointment.Status.COMPLETED)
        prescription_response = self.client.post(
            reverse("prescription_create", args=[record.pk]), {"notes": "Demo"}
        )
        prescription = Prescription.objects.get(record=record)
        self.assertRedirects(
            prescription_response, reverse("prescription_detail", args=[prescription.pk])
        )
        item_response = self.client.post(
            reverse("prescription_item_create", args=[prescription.pk]), {
                "medicine": self.medicine.pk, "quantity": "2", "dosage": "Demo",
                "frequency": "Demo", "instructions": "Thử nghiệm",
            },
        )
        self.assertRedirects(item_response, reverse("prescription_detail", args=[prescription.pk]))
        self.assertEqual(PrescriptionItem.objects.filter(prescription=prescription).count(), 1)

    def test_receptionist_can_create_patient(self):
        self.login_as(self.reception_user)
        response = self.client.post(reverse("patient_create"), {
            "patient_code": "BN503", "full_name": "Bệnh nhân giả lập mới",
        })
        self.assertRedirects(response, reverse("patient_list"))
        self.assertTrue(Patient.objects.filter(patient_code="BN503").exists())

    def test_doctor_cannot_manage_reception_or_admin_functions(self):
        self.login_as(self.doctor_user)
        for name in ("patient_list", "appointment_create", "medicine_create", "doctor_create"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)
        self.assertEqual(self.client.get(reverse("medicine_list")).status_code, 200)

    def test_doctor_requires_linked_doctor_profile(self):
        self.doctor.user = None
        self.doctor.save(update_fields=["user"])
        self.login_as(self.doctor_user)
        self.assertEqual(self.client.get(reverse("medical_record_create")).status_code, 403)

    def test_admin_remains_allowed_everywhere(self):
        self.login_as(self.admin)
        for name in (
            "patient_list", "doctor_create", "appointment_create", "medical_record_list",
            "medicine_create", "medicine_list",
        ):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 200)

    def test_non_staff_roles_have_no_admin_access(self):
        for user in (self.doctor_user, self.reception_user):
            self.login_as(user)
            response = self.client.get(reverse("admin:auth_user_changelist"))
            self.assertEqual(response.status_code, 302)

    def test_nav_respects_role(self):
        self.login_as(self.doctor_user)
        doctor_home = self.client.get(reverse("home"))
        self.assertContains(doctor_home, "Hồ sơ khám")
        self.assertNotContains(doctor_home, "Quản lý tài khoản")
        self.login_as(self.reception_user)
        reception_home = self.client.get(reverse("home"))
        self.assertContains(reception_home, "Bệnh nhân")
        self.assertNotContains(reception_home, "Danh mục thuốc")
