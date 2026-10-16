FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY service_a ./service_a
COPY service_b ./service_b
COPY logging.json ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000 8001

CMD ["uvicorn", "service_a.main:app", "--host", "0.0.0.0", "--port", "8000"]
