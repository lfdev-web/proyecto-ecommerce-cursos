FROM python:3.12-slim

LABEL maintainer="Equipo Cursos TEC Ecuador"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ─────────────────────────────────────────────────────────────────────────────
# PASO 1 CRÍTICO: Librerías de sistema ANTES de pip install
# Sin estas librerías, el contenedor arranca pero falla en runtime:
#
# Grupo A — Conexión a PostgreSQL (psycopg2):
#   libpq-dev, gcc
#
# Grupo B — Renderizado HTML/CSS → PDF (WeasyPrint):
#   libcairo2, libpango-1.0-0, libpangocairo-1.0-0, libgdk-pixbuf2.0-0,
#   libffi-dev, shared-mime-info
#
# Grupo C — Fuentes tipográficas (WeasyPrint "Missing Font Syndrome"):
#   fonts-liberation   → equivalente libre de Arial, Times New Roman, Courier
#   fonts-dejavu-core  → fuentes vectoriales robustas para tablas y datos
#   Sin estas fuentes, Pango usa fallback del sistema → PDF con layout roto
# ─────────────────────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Grupo A: PostgreSQL
    libpq-dev \
    gcc \
    # Grupo B: WeasyPrint — renderizado gráfico
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Grupo C: Fuentes tipográficas — CRÍTICO para PDFs con texto limpio
    fonts-liberation \
    fonts-dejavu-core \
    # Utilidades
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────────────────────────────────────────
# PASO 2: Dependencias Python en capa separada (optimización de cache Docker)
# Al copiar requirements.txt ANTES del código fuente, Docker cachea esta capa.
# Si solo cambias código Python (no dependencias), el rebuild es instantáneo.
# ─────────────────────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# PASO 3: Código fuente (cambia con frecuencia — última capa)
# ─────────────────────────────────────────────────────────────────────────────
COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
