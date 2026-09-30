# TatRaksha API. Build from the REPO ROOT (the API reads ai/, data/, geospatial/ and infrastructure/bigquery/ at runtime):
#   docker build -f services/api/Dockerfile -t tatraksha-api .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 REPO_ROOT=/repo PORT=8080
WORKDIR /repo/services/api
COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Runtime assets: versioned prompts + schemas, replay datasets + state adapters, Earth Engine scripts, BQ schemas
COPY ai /repo/ai
COPY data /repo/data
COPY geospatial /repo/geospatial
COPY infrastructure/bigquery /repo/infrastructure/bigquery
COPY services/api/app ./app
RUN useradd --uid 10001 --no-create-home app \
 && mkdir -p /repo/services/api/.data /repo/data/cache \
 && chown -R app /repo/services/api/.data /repo/data/cache
USER app
ENV PATH=/repo/services/api/.venv/bin:$PATH
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
