from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.using(schema_editor.connection.alias).get_or_create(name="Bác sĩ")
    Group.objects.using(schema_editor.connection.alias).get_or_create(name="Lễ tân")


class Migration(migrations.Migration):
    dependencies = [
        ("clinic", "0003_medicalrecord_medicine_prescription_prescriptionitem"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="doctor",
            name="user",
            field=models.OneToOneField(
                blank=True,
                help_text="Chọn tài khoản thuộc nhóm Bác sĩ; mỗi tài khoản chỉ gắn với một bác sĩ.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="doctor_profile",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Tài khoản đăng nhập",
            ),
        ),
        migrations.RunPython(create_roles, migrations.RunPython.noop),
    ]
