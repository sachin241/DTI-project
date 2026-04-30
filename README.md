# 📊 Price Tracker — Smart Multi-Platform Price Tracker

> Track Flipkart · Amazon India · Myntra · Snapdeal — all in one place.

---

## 🚀 What's Included

- FastAPI web dashboard with login, track, compare, analytics
- Selenium scraping for Flipkart, Amazon.in, Myntra, Snapdeal
- SQLite storage with safe context-managed connections
- HTML email alerts via Gmail SMTP
- APScheduler background price polling every 6 hours
- Deployment-ready container support and environment-driven config

---

## ⚡ Quick Start

```bash
python -m pip install -r requirements.txt

export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export SENDER_EMAIL="your_gmail@gmail.com"
export APP_PASSWORD="your_gmail_app_password"
export APP_BASE_URL="http://127.0.0.1:8000"

# Optional: Google OAuth
export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."
export GOOGLE_REDIRECT_URI="$APP_BASE_URL/auth/google/callback"

uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`

---

## 🚢 Deploy to Render.com

This repository includes a `Dockerfile` for container deployment.

1. Create a Render Web Service using Docker.
2. Set environment variables:
   - `SECRET_KEY`
   - `SENDER_EMAIL`
   - `APP_PASSWORD`
   - `APP_BASE_URL`
   - `GOOGLE_CLIENT_ID` (optional)
   - `GOOGLE_CLIENT_SECRET` (optional)
   - `GOOGLE_REDIRECT_URI` (optional)
3. Deploy.

Render provides `PORT` automatically, and the container command uses it.

---

## 📋 Supported Platforms

| Platform   | Domain          | Example Selectors                 |
|------------|-----------------|-----------------------------------|
| Flipkart   | flipkart.com    | `div._30jeq3`, `div.Nx9bqj`       |
| Amazon.in  | amazon.in       | `span#priceToPay span.a-offscreen`|
| Myntra     | myntra.com      | `span.pdp-price strong`           |
| Snapdeal   | snapdeal.com    | `span#selling-price-id`           |

---

## 🔐 Deployment Notes

- Templates and DB path use absolute locations so the app works from any working directory.
- Session cookies can be secured in production with `SESSION_HTTPS_ONLY=true`.
- Email credentials are required in environment variables, and no defaults are hardcoded.
- `APP_BASE_URL` is used to build OAuth callback URLs when `GOOGLE_REDIRECT_URI` is not provided.

---

## 📂 File Overview

```
./main.py
./scraper.py
./database.py
./email_service.py
./scheduler.py
./requirements.txt
./Dockerfile
./render.yaml
```

