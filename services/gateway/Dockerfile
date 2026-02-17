FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY services /app/services
COPY frontend /app/frontend

CMD ["uvicorn", "services.gateway.app.main:app", "--host", "0.0.0.0", "--port", "8080"]

