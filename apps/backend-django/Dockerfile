# syntax=docker/dockerfile:1

# --------------------------------------------------------------------------- #
# Etapa base: común a desarrollo y producción
# --------------------------------------------------------------------------- #
FROM python:3.13-slim-trixie AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# libpq: cliente de PostgreSQL. build-essential se necesita solo si alguna
# dependencia hay que compilarla.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------------------------------- #
# Desarrollo: el código se monta como volumen desde el host
# --------------------------------------------------------------------------- #
FROM base AS development

COPY requirements/ /app/requirements/
RUN pip install --upgrade pip && pip install -r requirements/local.txt

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --------------------------------------------------------------------------- #
# Producción: el código va dentro de la imagen y corre con gunicorn
# --------------------------------------------------------------------------- #
FROM base AS production

COPY requirements/ /app/requirements/
RUN pip install --upgrade pip && pip install -r requirements/production.txt

COPY . /app

# Usuario sin privilegios
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
