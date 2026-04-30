FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV CHROME_BINARY=/usr/bin/chromium

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        libnss3 \
        libgconf-2-4 \
        libx11-6 \
        libx11-xcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxss1 \
        libxtst6 \
        libglib2.0-0 \
        libasound2 \
        libatk1.0-0 \
        libcups2 \
        libgbm1 \
        libpangocairo-1.0-0 \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
