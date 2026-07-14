FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd -m appuser && mkdir -p /data && chown appuser:appuser /data
USER appuser

ENV DATABASE_URL=sqlite:////data/billing_report.db
ENV ION_TOKEN_CACHE_PATH=/data/.ion_token_cache.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
