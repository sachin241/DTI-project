from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from scraper import get_flipkart_price
from database import insert_price, init_db, get_last_price
from database import get_tracked_products_by_email
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "submitted": False
        }
    )


@app.post("/", response_class=HTMLResponse)
def fetch_price(
    request: Request,
    product_url: str = Form(...),
    email: str = Form(...)
):
    # 1️⃣ Get previous price
    old_price = get_last_price(product_url)

    # 2️⃣ Scrape current price
    price_text, price_number = get_flipkart_price(product_url)

    if not price_text:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Could not fetch price. Please try again."
            }
        )

    # 3️⃣ Compare prices
    if old_price is None:
        message = "🆕 First time tracking this product"
    else:
        if price_number < old_price:
            message = f"🎉 Price dropped from ₹{old_price} to {price_text}"
        elif price_number > old_price:
            message = f"📈 Price increased from ₹{old_price} to {price_text}"
        else:
            message = "⏸️ Price unchanged"

    # 4️⃣ SAVE new price (THIS IS THE LINE YOU ASKED ABOUT)
    insert_price(product_url, email, price_number)
    products = get_tracked_products_by_email(email)
    # 5️⃣ Return response
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "price": price_text,
            "message": message,
            "products": products,
            "submitted": True
        }
    )