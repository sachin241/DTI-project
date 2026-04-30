# database.py
import os
import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.getenv("DB_NAME", "prices.db")
DB_PATH = DB_NAME if os.path.isabs(DB_NAME) else os.path.join(BASE_DIR, DB_NAME)


@contextmanager
def get_db():
    """Context manager for safe database connections with auto-close."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        # Products table — now includes platform field
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                url          TEXT NOT NULL,
                platform     TEXT NOT NULL DEFAULT 'flipkart',
                product_name TEXT,
                email        TEXT NOT NULL,
                price        INTEGER NOT NULL,
                target_price INTEGER,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add platform and product_name columns if upgrading from old schema
        existing = {row[1] for row in cursor.execute("PRAGMA table_info(products)")}
        if "platform" not in existing:
            cursor.execute("ALTER TABLE products ADD COLUMN platform TEXT NOT NULL DEFAULT 'flipkart'")
        if "product_name" not in existing:
            cursor.execute("ALTER TABLE products ADD COLUMN product_name TEXT")

        # User logins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_logins (
                email        TEXT PRIMARY KEY,
                provider     TEXT,
                last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alert log — tracks every email sent so we don't spam
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                url        TEXT NOT NULL,
                email      TEXT NOT NULL,
                price      INTEGER NOT NULL,
                sent_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def insert_price(url: str, email: str, price: int, target_price: Optional[int],
                 platform: str = "flipkart", product_name: str = None):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO products (url, email, price, target_price, platform, product_name)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (url, email, price, target_price, platform, product_name)
        )


def get_last_price(url: str) -> Optional[int]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT price FROM products WHERE url=? ORDER BY created_at DESC LIMIT 1",
            (url,)
        ).fetchone()
        return row["price"] if row else None


def get_price_history(url: str, email: str, limit: int = 30) -> List[dict]:
    """Return price history for a specific product."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT price, created_at FROM products
            WHERE url=? AND email=?
            ORDER BY created_at DESC LIMIT ?
            """,
            (url, email, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_tracked_products_by_email(email: str) -> List[sqlite3.Row]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT url, platform, product_name, price, target_price, created_at
            FROM products
            WHERE email = ?
              AND id IN (
                  SELECT MAX(id) FROM products
                  WHERE email = ?
                  GROUP BY url
              )
            ORDER BY created_at DESC
            """,
            (email, email)
        ).fetchall()
        return [dict(r) for r in rows]


def get_price_rows_by_email(email: str, limit: int = 300) -> List[dict]:
    """Return raw historical rows for analytics charts."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT url, platform, product_name, price, target_price, created_at
            FROM products
            WHERE email = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (email, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_tracked_products() -> List[dict]:
    """Return one latest record per (url, email) pair for the scheduler."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT url, email, target_price, platform, product_name
            FROM products
            WHERE id IN (
                SELECT MAX(id) FROM products
                GROUP BY url, email
            )
            """
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_user_login(email: str, provider: str):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO user_logins (email, provider, last_login_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(email) DO UPDATE SET
                provider = excluded.provider,
                last_login_at = CURRENT_TIMESTAMP
            """,
            (email, provider),
        )


def get_trusted_users_count() -> int:
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM user_logins").fetchone()[0]


def log_alert_sent(url: str, email: str, price: int):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO alert_log (url, email, price) VALUES (?, ?, ?)",
            (url, email, price)
        )


def was_alert_sent_recently(url: str, email: str, hours: int = 24) -> bool:
    """Prevent duplicate alerts within the given window."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM alert_log
            WHERE url=? AND email=?
              AND sent_at > datetime('now', ? || ' hours')
            LIMIT 1
            """,
            (url, email, f"-{hours}")
        ).fetchone()
        return row is not None


# Backward-compatible alias
get_all_products = get_all_tracked_products
