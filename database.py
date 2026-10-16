"""
database.py
Trendyol AI Manager için yerel SQLite veritabanı.
Kullanıcıları, işlenen fotoğrafları, oluşturulan ilanları ve kullanım istatistiklerini kaydeder.
"""

import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "trendyol_manager.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Kullanıcılar Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        role TEXT DEFAULT 'Satıcı',
        status TEXT DEFAULT 'Aktif',
        store_name TEXT DEFAULT '',
        total_photos INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 0,
        last_active TIMESTAMP
    )
    """)
    
    # Mevcut veritabanı varsa yeni sütunları güvenle ekle
    for col_def in [
        ("role", "TEXT DEFAULT 'Satıcı'"),
        ("status", "TEXT DEFAULT 'Aktif'"),
        ("store_name", "TEXT DEFAULT ''")
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_def[0]} {col_def[1]}")
        except Exception:
            pass
    
    # 2. İşlenen Ürünler & Fotoğraflar Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        product_title TEXT,
        has_lifestyle_render INTEGER DEFAULT 0,
        created_at TIMESTAMP
    )
    """)
    
    # 3. Canlı Sistem Logları Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT,
        message TEXT,
        timestamp TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def log_user_action(user_id: int, first_name: str, username: str, action: str = "photo"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    
    cursor.execute("SELECT user_id, total_photos, total_questions FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        if action == "photo":
            cursor.execute("UPDATE users SET first_name = ?, username = ?, total_photos = total_photos + 1, last_active = ? WHERE user_id = ?",
                           (first_name, username, now, user_id))
        else:
            cursor.execute("UPDATE users SET first_name = ?, username = ?, total_questions = total_questions + 1, last_active = ? WHERE user_id = ?",
                           (first_name, username, now, user_id))
    else:
        photos = 1 if action == "photo" else 0
        questions = 1 if action == "question" else 0
        cursor.execute("INSERT INTO users (user_id, first_name, username, role, status, store_name, total_photos, total_questions, last_active) VALUES (?, ?, ?, 'Satıcı', 'Aktif', '', ?, ?, ?)",
                       (user_id, first_name, username, photos, questions, now))
        
    conn.commit()
    conn.close()


def add_or_update_user(user_id: int, first_name: str, username: str, role: str = "Satıcı", status: str = "Aktif", store_name: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    clean_username = username.lstrip("@").strip()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        cursor.execute("""
        UPDATE users SET first_name = ?, username = ?, role = ?, status = ?, store_name = ?, last_active = ?
        WHERE user_id = ?
        """, (first_name, clean_username, role, status, store_name, now, user_id))
    else:
        cursor.execute("""
        INSERT INTO users (user_id, first_name, username, role, status, store_name, total_photos, total_questions, last_active)
        VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?)
        """, (user_id, first_name, clean_username, role, status, store_name, now))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def set_user_status(user_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()


def record_product(user_id: int, user_name: str, product_title: str, has_lifestyle: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute("INSERT INTO product_logs (user_id, user_name, product_title, has_lifestyle_render, created_at) VALUES (?, ?, ?, ?, ?)",
                   (user_id, user_name, product_title, 1 if has_lifestyle else 0, now))
    conn.commit()
    conn.close()


def add_system_log(level: str, message: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute("INSERT INTO system_logs (level, message, timestamp) VALUES (?, ?, ?)", (level, message, now))
    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_logs")
    total_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT user_id, first_name, username, role, status, store_name, total_photos, last_active FROM users ORDER BY last_active DESC LIMIT 50")
    recent_users = cursor.fetchall()
    
    cursor.execute("SELECT id, user_name, product_title, has_lifestyle_render, created_at FROM product_logs ORDER BY created_at DESC LIMIT 20")
    recent_products = cursor.fetchall()
    
    cursor.execute("SELECT level, message, timestamp FROM system_logs ORDER BY id DESC LIMIT 30")
    recent_logs = cursor.fetchall()
    
    conn.close()
    return {
        "total_users": total_users,
        "total_products": total_products,
        "recent_users": recent_users,
        "recent_products": recent_products,
        "recent_logs": recent_logs
    }

init_db()
