FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG APP_UID=100
ARG APP_GID=101
RUN addgroup --system --gid "${APP_GID}" appgroup && \
    adduser --system --uid "${APP_UID}" --gid "${APP_GID}" appuser

COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup alembic ./alembic
COPY --chown=appuser:appgroup alembic.ini .
COPY --chown=appuser:appgroup entrypoint.sh .
RUN chmod 0550 entrypoint.sh
RUN mkdir -p /app/storage && \
    chown appuser:appgroup /app/storage && \
    chmod 0750 /app/storage

USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
