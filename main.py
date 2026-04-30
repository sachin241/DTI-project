# main.py
import os
import secrets
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from scraper import get_product_price
from database import (
    insert_price, init_db, get_last_price,
    get_tracked_products_by_email, upsert_user_login, get_trusted_users_count,
    was_alert_sent_recently, log_alert_sent,
    get_price_rows_by_email,
)
from email_service import send_price_alert
from scheduler import start_price_scheduler, stop_price_scheduler

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", f"{APP_BASE_URL}/auth/google/callback")
SESSION_HTTPS_ONLY   = os.getenv("SESSION_HTTPS_ONLY", "false").lower() in ("1", "true", "yes")

app.add_middleware(
    SessionMiddleware,
    secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32)),
    max_age    = 60 * 60 * 24 * 7,
    same_site  = "lax",
    https_only = SESSION_HTTPS_ONLY,
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

LOGGED_IN_USERS: set = set()


# ── Helpers ───────────────────────────────────────────────────────────────────

def current_user(request: Request):
    return request.session.get("user")


def require_login(request: Request):
    if not current_user(request):
        return RedirectResponse(url="/login", status_code=302)
    return None


def base_ctx(request: Request, user, active: str = "", extra: dict = None) -> dict:
    """Build template context with variables shared by every page."""
    ctx = {
        "request":         request,
        "user":            user,
        "active":          active,
        "logged_in_count": len(LOGGED_IN_USERS),
        "trusted_count":   get_trusted_users_count(),
        "email_alerts_enabled": bool(os.getenv("SENDER_EMAIL")) and bool(os.getenv("APP_PASSWORD")),
    }
    if extra:
        ctx.update(extra)
    return ctx


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    init_db()
    start_price_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_price_scheduler()


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = None):
    if current_user(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request, "user": None, "active": "",
        "error": error, "google_enabled": bool(GOOGLE_CLIENT_ID),
    })


@app.post("/login", response_class=HTMLResponse)
def do_login(request: Request, email: str = Form(...), password: str = Form(...)):
    if not email or len(password) < 6:
        return templates.TemplateResponse("login.html", {
            "request": request, "user": None, "active": "",
            "error": "Password must be at least 6 characters.",
            "google_enabled": bool(GOOGLE_CLIENT_ID),
        }, status_code=400)

    request.session["user"] = {
        "email":    email,
        "name":     email.split("@")[0].replace(".", " ").title(),
        "picture":  None,
        "provider": "free",
    }
    LOGGED_IN_USERS.add(email.lower())
    upsert_user_login(email.lower(), "free")
    return RedirectResponse(url="/", status_code=302)


@app.get("/logout")
def logout(request: Request):
    user = current_user(request)
    if user and user.get("email"):
        LOGGED_IN_USERS.discard(user["email"].lower())
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ── Google OAuth ──────────────────────────────────────────────────────────────

@app.get("/auth/google")
def google_login(request: Request):
    if not GOOGLE_CLIENT_ID:
        return RedirectResponse(
            url="/login?error=Google+OAuth+not+configured.+Set+GOOGLE_CLIENT_ID.",
            status_code=302,
        )
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    params = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid+email+profile"
        f"&state={state}"
        f"&access_type=offline&prompt=select_account"
    )
    return RedirectResponse(url=params, status_code=302)


@app.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: str  = None,
    state: str = None,
    error: str = None,
):
    if error or not code:
        return RedirectResponse(url="/login?error=Google+sign-in+cancelled.", status_code=302)
    if state != request.session.get("oauth_state"):
        return RedirectResponse(url="/login?error=OAuth+state+mismatch.", status_code=302)

    async with httpx.AsyncClient() as client:
        token_data = (await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code":          code,
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  GOOGLE_REDIRECT_URI,
                "grant_type":    "authorization_code",
            },
        )).json()

        if "error" in token_data:
            return RedirectResponse(
                url=f"/login?error=Google+token+error:+{token_data['error']}",
                status_code=302,
            )

        userinfo = (await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )).json()

    request.session["user"] = {
        "email":    userinfo.get("email"),
        "name":     userinfo.get("name"),
        "picture":  userinfo.get("picture"),
        "provider": "google",
    }
    if userinfo.get("email"):
        LOGGED_IN_USERS.add(userinfo["email"].lower())
        upsert_user_login(userinfo["email"].lower(), "google")
    request.session.pop("oauth_state", None)
    return RedirectResponse(url="/", status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  APP ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    r = require_login(request)
    if r: return r
    return templates.TemplateResponse(
        "index.html",
        base_ctx(request, current_user(request), active="home"),
    )


# ── Track ─────────────────────────────────────────────────────────────────────

@app.get("/track", response_class=HTMLResponse)
def track_page(request: Request):
    r = require_login(request)
    if r: return r
    return templates.TemplateResponse(
        "track.html",
        base_ctx(request, current_user(request), active="track"),
    )


@app.post("/track", response_class=HTMLResponse)
def fetch_price(
    request:      Request,
    product_url:  str = Form(...),
    email:        str = Form(...),
    target_price: int = Form(...),
):
    r = require_login(request)
    if r: return r
    user = current_user(request)

    price_text, price_number, platform, product_name = get_product_price(product_url)

    if price_text and price_number:
        old_price = get_last_price(product_url)

        if old_price is None:
            status  = "first"
            message = "First time tracking this product"
        elif price_number < old_price:
            status  = "drop"
            message = f"Price dropped from ₹{old_price:,} to {price_text} 📉"
        elif price_number > old_price:
            status  = "rise"
            message = f"Price increased from ₹{old_price:,} to {price_text} 📈"
        else:
            status  = "same"
            message = "Price unchanged"

        target_hit = price_number <= target_price
        alert_result = None
        alert_hint = None
        if target_hit:
            message += " — 🎯 Target price reached!"
            if was_alert_sent_recently(product_url, email, hours=24):
                alert_result = "skipped"
                alert_hint = "Alert already sent in the last 24 hours, so duplicate email was skipped."
            else:
                sent = send_price_alert(
                    email         = email,
                    product_url   = product_url,
                    current_price = price_number,
                    target_price  = target_price,
                    platform      = platform,
                    product_name  = product_name,
                )
                if sent:
                    log_alert_sent(product_url, email, price_number)
                    alert_result = "sent"
                    alert_hint = f"Email alert sent successfully to {email}."
                else:
                    alert_result = "failed"
                    alert_hint = (
                        "Target reached, but email could not be sent. "
                        "Check SENDER_EMAIL / APP_PASSWORD in environment settings."
                    )

        insert_price(product_url, email, price_number, target_price, platform, product_name)
        products = get_tracked_products_by_email(email)

        return templates.TemplateResponse("track.html", base_ctx(
            request, user, active="track", extra={
                "price":        price_text,
                "price_num":    price_number,
                "message":      message,
                "status":       status,
                "target_hit":   target_hit,
                "alert_result": alert_result,
                "alert_hint":   alert_hint,
                "platform":     platform,
                "product_name": product_name,
                "products":     products,
            }
        ))

    return templates.TemplateResponse("track.html", base_ctx(
        request, user, active="track", extra={
            "error": "Could not fetch price. Check the URL — supported platforms: Flipkart, Amazon.in, Myntra, Snapdeal.",
        }
    ))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    r = require_login(request)
    if r: return r
    user     = current_user(request)
    products = get_tracked_products_by_email(user["email"])
    return templates.TemplateResponse(
        "dashboard.html",
        base_ctx(request, user, active="dashboard", extra={"products": products}),
    )


# ── Compare ───────────────────────────────────────────────────────────────────

@app.get("/compare", response_class=HTMLResponse)
def compare_page(request: Request):
    r = require_login(request)
    if r: return r
    return templates.TemplateResponse(
        "compare.html",
        base_ctx(request, current_user(request), active="compare"),
    )


@app.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request):
    r = require_login(request)
    if r: return r
    user = current_user(request)
    rows = get_price_rows_by_email(user["email"], limit=300)
    return templates.TemplateResponse(
        "analytics.html",
        base_ctx(request, user, active="analytics", extra={"rows": rows}),
    )


@app.get("/api/compare")
def price_comparison_api(q: str = ""):
    comparisons = [
        {
            "product": "iPhone 17 Pro Max (128GB)",
            "prices": [
                {"site": "Flipkart", "price": 69999},
                {"site": "Amazon",   "price": 68999},
            ],
            "lowest": "Amazon", "savings": 1000,
        },
        {
            "product": "Samsung Galaxy S26 Ultra (256GB)",
            "prices": [
                {"site": "Flipkart", "price": 74999},
                {"site": "Amazon",   "price": 77000},
                {"site": "Snapdeal", "price": 73500},
            ],
            "lowest": "Snapdeal", "savings": 3500,
        },
        {
            "product": "Sony WH-1000XM6",
            "prices": [
                {"site": "Flipkart", "price": 28990},
                {"site": "Amazon",   "price": 26490},
                {"site": "Myntra",   "price": 27999},
            ],
            "lowest": "Amazon", "savings": 2500,
        },
    ]
    return JSONResponse({"comparisons": comparisons})
