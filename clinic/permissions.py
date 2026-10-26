"""Quyền nghiệp vụ phía server. Không dựa vào việc ẩn nút ở giao diện."""

from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_RECEPTION = "reception"

GROUP_DOCTOR = "Bác sĩ"
GROUP_RECEPTION = "Lễ tân"


def user_has_role(user, role):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True  # Quản trị viên có quyền truy cập mọi chức năng.
    if role == ROLE_ADMIN:
        return False
    if role not in (ROLE_DOCTOR, ROLE_RECEPTION):
        return False
    group_name = GROUP_DOCTOR if role == ROLE_DOCTOR else GROUP_RECEPTION
    return user.groups.filter(name=group_name).exists()


def role_required(*roles):
    def decorate(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
            if not any(user_has_role(request.user, role) for role in roles):
                raise PermissionDenied("Tài khoản không có quyền truy cập chức năng này.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorate


def role_flags(request):
    user = request.user
    return {
        "role_admin": user_has_role(user, ROLE_ADMIN),
        "role_doctor": user_has_role(user, ROLE_DOCTOR),
        "role_reception": user_has_role(user, ROLE_RECEPTION),
    }
