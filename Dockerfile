FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ung dung Django khong can chay voi quyen root.
RUN useradd --create-home --shell /usr/sbin/nologin clinicuser \
    && mkdir -p /app/staticfiles \
    && chown -R clinicuser:clinicuser /app
USER clinicuser

EXPOSE 8000
