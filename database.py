# database.py
import sqlite3

DB_NAME = "prices.db"


def get_connection():
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        return conn
    except Exception as e:
        print("Database connection error:", e)
        return None


def init_db():
    conn = get_connection()
    if conn is None:
        raise Exception("Failed to create database connection")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            email TEXT NOT NULL,
            price INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def insert_price(url, email, price):
    conn = get_connection()
    if conn is None:
        raise Exception("Database connection failed")

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (url, email, price)
        VALUES (?, ?, ?)
        """,
        (url, email, price)
    )

    conn.commit()
    conn.close()


def get_last_price(url):
    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT price FROM products
        WHERE url = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (url,)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]   # previous price
    return None        # first time
def get_tracked_products_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT url, price, created_at
        FROM products
        WHERE email = ?
          AND id IN (
              SELECT MAX(id)
              FROM products
              WHERE email = ?
              GROUP BY url
          )
        ORDER BY created_at DESC
    """, (email, email))

    rows = cursor.fetchall()
    conn.close()
    return rows