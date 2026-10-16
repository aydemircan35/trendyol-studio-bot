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
        ("store_name", "TEXT DEFAULT ''"),
        ("password", "TEXT DEFAULT ''")
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


def add_or_update_user(user_id: int, first_name: str, username: str, role: str = "Satıcı", status: str = "Aktif", store_name: str = "", password: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    clean_username = username.lstrip("@").strip()
    
    cursor.execute("SELECT user_id, password FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    final_pass = password
    if not final_pass:
        if row and row[1]:
            final_pass = row[1]
        else:
            easy = generate_easy_credentials(first_name=first_name, username=clean_username)
            final_pass = easy["password"]
            
    if row:
        cursor.execute("""
        UPDATE users SET first_name = ?, username = ?, role = ?, status = ?, store_name = ?, password = ?, last_active = ?
        WHERE user_id = ?
        """, (first_name, clean_username, role, status, store_name, final_pass, now, user_id))
    else:
        cursor.execute("""
        INSERT INTO users (user_id, first_name, username, password, role, status, store_name, total_photos, total_questions, last_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
        """, (user_id, first_name, clean_username, final_pass, role, status, store_name, now))
    conn.commit()
    conn.close()
    return final_pass


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


def generate_easy_credentials(first_name: str = "", username: str = "") -> dict:
    """
    Çok kolay, akılda kalıcı ve pratik bir kullanıcı adı & 4 haneli PIN şifre üretir.
    """
    import random
    import re
    
    # Kolay kullanıcı adı
    raw_name = username or first_name or "satici"
    clean = re.sub(r"[^a-zA-Z0-9]", "", raw_name.lower())
    if not clean:
        clean = "satici"
    
    # Kısa ve kolay ad
    clean = clean[:10]
    easy_username = f"{clean}{random.randint(10, 99)}" if len(clean) < 5 else clean
    
    # Kolay ve akılda kalıcı 4 haneli PIN şifre (Örn: 1234, 2026, 7788, 5544)
    easy_pins = ["1234", "2026", "1010", "5555", "7788", "9900", "4433", "2211", "8822"]
    easy_password = random.choice(easy_pins) if random.random() < 0.4 else str(random.randint(1000, 9999))
    
    return {
        "username": easy_username,
        "password": easy_password
    }


def create_or_get_user_account(user_id: int, first_name: str, username: str, custom_password: str = None, custom_username: str = None, force_regenerate: bool = False):
    """
    Kullanıcıya kolay kullanıcı adı ve şifre üretir veya mevcut olanı döner.
    İsterse custom_password ve custom_username belirleyebilir.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    
    cursor.execute("SELECT user_id, first_name, username, password, role, status FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    # Zaten şifresi var ve güncelleme istenmediyse
    if row and row[3] and not force_regenerate and not custom_password and not custom_username:
        conn.close()
        return {
            "user_id": row[0],
            "first_name": row[1],
            "username": row[2],
            "password": row[3],
            "role": row[4],
            "status": row[5],
            "is_new": False
        }
    
    # Kolay belirleme veya özel belirleme
    easy = generate_easy_credentials(first_name=first_name, username=username)
    final_username = (custom_username or (row[2] if row and row[2] else (username or "").strip().lstrip("@")) or easy["username"]).lower()
    final_password = custom_password or (row[3] if row and row[3] and not force_regenerate else easy["password"])
    
    if row:
        cursor.execute("UPDATE users SET password = ?, username = ?, first_name = ?, last_active = ? WHERE user_id = ?",
                       (final_password, final_username, first_name, now, user_id))
    else:
        cursor.execute("""
        INSERT INTO users (user_id, first_name, username, password, role, status, store_name, total_photos, total_questions, last_active)
        VALUES (?, ?, ?, ?, 'Satıcı', 'Aktif', 'Trendyol Mağazası', 0, 0, ?)
        """, (user_id, first_name, final_username, final_password, now))
        
    conn.commit()
    conn.close()
    
    return {
        "user_id": user_id,
        "first_name": first_name,
        "username": final_username,
        "password": final_password,
        "role": "Satıcı",
        "status": "Aktif",
        "is_new": True if not row else False
    }


def update_user_credentials(user_id_or_username, new_password: str = None, new_username: str = None):
    """
    Kullanıcının şifresini veya kullanıcı adını günceller.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    clean_target = str(user_id_or_username).strip().lstrip("@")
    
    cursor.execute("SELECT user_id, username, password FROM users WHERE username = ? OR CAST(user_id AS TEXT) = ?",
                   (clean_target, clean_target))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "Kullanıcı bulunamadı!"}
        
    uid = row[0]
    final_u = (new_username.strip().lstrip("@").lower()) if new_username and new_username.strip() else row[1]
    final_p = new_password.strip() if new_password and new_password.strip() else row[2]
    
    cursor.execute("UPDATE users SET username = ?, password = ? WHERE user_id = ?", (final_u, final_p, uid))
    conn.commit()
    conn.close()
    
    return {"success": True, "user_id": uid, "username": final_u, "password": final_p}


def register_web_user(first_name: str, store_name: str, username: str = None, password: str = None, telegram_id: int = None):
    """
    Web kayıt ekranından yeni satıcı hesabı oluşturur. Kullanıcı adı ve şifre boşsa kolay otomatik belirler.
    """
    import random
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    
    uid = telegram_id or random.randint(100000000, 999999999)
    easy = generate_easy_credentials(first_name=first_name, username=username)
    
    final_username = (username.strip().lstrip("@").lower()) if username and username.strip() else easy["username"]
    final_password = password.strip() if password and password.strip() else easy["password"]
    
    # Kullanıcı adı çakışma kontrolü
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (final_username,))
    if cursor.fetchone():
        final_username = f"{final_username}_{random.randint(10, 99)}"
        
    cursor.execute("""
    INSERT INTO users (user_id, first_name, username, password, role, status, store_name, total_photos, total_questions, last_active)
    VALUES (?, ?, ?, ?, 'Satıcı', 'Aktif', ?, 0, 0, ?)
    """, (uid, first_name.strip(), final_username, final_password, store_name.strip() if store_name else "Trendyol Mağazası", now))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "user_id": uid,
        "first_name": first_name.strip(),
        "username": final_username,
        "password": final_password,
        "store_name": store_name.strip()
    }


def verify_login(username_or_id: str, password_attempt: str):
    """
    Giriş bilgilerini kontrol eder:
    - Admin (admin / trendyol123)
    - Kayıtlı Satıcılar (kullanıcı adı / şifre)
    """
    admin_u = os.getenv("ADMIN_USERNAME", "admin")
    admin_p = os.getenv("ADMIN_PASSWORD", "trendyol123")
    
    if username_or_id.strip() == admin_u and password_attempt.strip() == admin_p:
        return {"success": True, "role": "Yönetici (Admin)", "name": "Sistem Yöneticisi", "user_id": 1}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    clean_u = username_or_id.strip().lstrip("@")
    
    cursor.execute("""
    SELECT user_id, first_name, username, password, role, status, store_name
    FROM users
    WHERE (username = ? OR CAST(user_id AS TEXT) = ?) AND status = 'Aktif'
    """, (clean_u, clean_u))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[3] and row[3].strip() == password_attempt.strip():
        return {
            "success": True,
            "role": row[4] or "Satıcı",
            "name": row[1] or row[2],
            "store_name": row[6] or "",
            "user_id": row[0]
        }
        
    return {"success": False, "error": "Geçersiz kullanıcı adı veya şifre!"}


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
    
    cursor.execute("SELECT user_id, first_name, username, password, role, status, store_name, total_photos, last_active FROM users ORDER BY last_active DESC LIMIT 50")
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
