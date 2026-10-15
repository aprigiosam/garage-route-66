# syntax=docker/dockerfile:1

# --- build: instala dependências travadas no uv.lock e gera os estáticos -------
FROM ghcr.io/astral-sh/uv:0.13.1 AS uv

FROM python:3.12-slim-trixie AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
# Dependências antes do código: a camada fica em cache enquanto o uv.lock não mudar.
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project
COPY manage.py ./
COPY config ./config
COPY oficina ./oficina
COPY balcao ./balcao
RUN DJANGO_SECRET_KEY=somente-build DJANGO_STATIC_MANIFEST=1 \
    /app/.venv/bin/python manage.py collectstatic --noinput

# --- runtime: só o necessário, sem uv nem cache, usuário sem privilégios -------
FROM python:3.12-slim-trixie
RUN useradd --system --uid 10001 --no-create-home app \
    && mkdir /data && chown app /data
WORKDIR /app
COPY --from=build /app /app
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DJANGO_STATIC_MANIFEST=1 \
    DJANGO_DB_PATH=/data/db.sqlite3
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/saude/', timeout=2)"]
# Migração na subida (instância única). 2 workers: sobra para 1 usuária e cabe em ~100 MB.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 2 --worker-tmp-dir /dev/shm --access-logfile -"]
