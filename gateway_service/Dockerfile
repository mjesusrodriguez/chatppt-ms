# Dockerfile
FROM python:3.11-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar la carpeta common
COPY common ./common

# Copiar la carpeta templates y static
COPY templates/ ./templates
COPY static/ ./static

# Copiar solo el contenido del microservicio
COPY gateway_service/ .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 🔥 Línea clave para ver los print()
ENV PYTHONUNBUFFERED=1

# Exponer el puerto que usará Flask
EXPOSE 5000

# Comando para lanzar el microservicio
CMD ["python", "app.py"]