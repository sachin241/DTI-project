# scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re


def get_flipkart_price(url: str):
    """
    Fetch price from a Flipkart product page.
    Returns: (price_text, price_number)
    Example: ("₹74,900", 74900)
    """

    # Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(url)
        time.sleep(4)  # allow JS to load

        # Close login popup if it appears
        try:
            ActionChains(driver).send_keys("\ue00c").perform()  # ESC
        except:
            pass

        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)

        wait = WebDriverWait(driver, 25)
        price_text = None

        # ✅ METHOD 1: Official Flipkart price class
        try:
            price_el = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div._30jeq3")
                )
            )
            price_text = price_el.text.strip()
        except:
            pass

        # ✅ METHOD 2: Fallback – find any ₹ that looks like a real price
        if not price_text:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(),'₹')]")
            for el in elements:
                txt = el.text.strip()
                # Match prices like ₹13,999 or ₹74900
                if re.fullmatch(r"₹\s?\d{1,3}(,\d{3})*", txt):
                    price_text = txt
                    break

        if not price_text:
            return None, None

        # Convert "₹74,900" → 74900
        price_number = int(
            price_text.replace("₹", "")
                      .replace(",", "")
                      .strip()
        )

        return price_text, price_number

    finally:
        driver.quit()