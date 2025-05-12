FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libpq-dev \
    python3-dev

WORKDIR /app

# Copiar la carpeta common
COPY common ./common

# Copiar solo el contenido del microservicio
COPY disc_parameter_service/ .

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_md

# 🔥 Línea clave para ver los print()
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "app.py"]