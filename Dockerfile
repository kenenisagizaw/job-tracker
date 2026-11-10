FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup alembic ./alembic
COPY --chown=appuser:appgroup alembic.ini .
COPY --chown=appuser:appgroup entrypoint.sh .
RUN chmod 0550 entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
