# Pinned base image digest; must publish an arm64 variant (verified at G0).
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Non-root runtime user.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /srv --shell /usr/sbin/nologin app

COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir --requirement /srv/requirements.txt

COPY app /srv/app

# Ledger volume mount point; owned by the non-root user.
RUN mkdir -p /data && chown -R app:app /srv /data

USER 10001:10001
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
