# Prospect Assist AI — container image (works on Render / Railway / Cloud Run / Fly).
FROM python:3.12-slim

# WeasyPrint needs native pango/cairo/gdk-pixbuf; fonts for the PDF.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
        libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data + trained models are committed, so no build-time setup is needed.
ENV PORT=8000
EXPOSE 8000

# Shell form so $PORT (injected by the host) is expanded.
CMD uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-8000}
