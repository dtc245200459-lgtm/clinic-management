"""Thiết lập bổ sung cho HTTPS thử nghiệm sau Nginx tại localhost.

Không thay thế settings.py và không dùng cấu hình này cho Internet thực tế.
"""

from .settings import *  # noqa: F401,F403

# Nginx ghi đè X-Forwarded-Proto trước khi chuyển đến Gunicorn.
# Tin header này chỉ phù hợp khi reverse proxy được kiểm soát.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
