from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/new/", views.patient_create, name="patient_create"),
    path("patients/<int:pk>/edit/", views.patient_update, name="patient_update"),
    path("patients/<int:pk>/delete/", views.patient_delete, name="patient_delete"),
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/new/", views.doctor_create, name="doctor_create"),
    path("doctors/<int:pk>/edit/", views.doctor_update, name="doctor_update"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/new/", views.appointment_create, name="appointment_create"),
    path("appointments/<int:pk>/edit/", views.appointment_update, name="appointment_update"),
    path("appointments/<int:pk>/cancel/", views.appointment_cancel, name="appointment_cancel"),
    path("records/", views.medical_record_list, name="medical_record_list"),
    path("records/new/", views.medical_record_create, name="medical_record_create"),
    path("records/<int:pk>/", views.medical_record_detail, name="medical_record_detail"),
    path("records/<int:pk>/edit/", views.medical_record_update, name="medical_record_update"),
    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/new/", views.medicine_create, name="medicine_create"),
    path("medicines/<int:pk>/edit/", views.medicine_update, name="medicine_update"),
    path("records/<int:record_pk>/prescription/new/", views.prescription_create, name="prescription_create"),
    path("prescriptions/<int:pk>/", views.prescription_detail, name="prescription_detail"),
    path("prescriptions/<int:pk>/edit/", views.prescription_update, name="prescription_update"),
    path("prescriptions/<int:pk>/items/new/", views.prescription_item_create, name="prescription_item_create"),
    path("prescriptions/<int:pk>/items/<int:item_pk>/edit/", views.prescription_item_update, name="prescription_item_update"),
]
