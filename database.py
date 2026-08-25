import sqlite3

def get_db():
    conn = sqlite3.connect('bot_data.db')
    return conn, conn.cursor()

def init_db():
    conn, c = get_db()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, referrer_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS channels (username TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gifts (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gift_history (user_id INTEGER, code TEXT, PRIMARY KEY(user_id, code))''')
    conn.commit()
    conn.close()

def add_user(user_id, referrer_id=None):
    conn, c = get_db()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_points(user_id):
    conn, c = get_db()
    c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def update_points(user_id, amount):
    conn, c = get_db()
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_channels():
    conn, c = get_db()
    c.execute("SELECT username FROM channels")
    res = [row[0] for row in c.fetchall()]
    conn.close()
    return res

def add_channel(username):
    conn, c = get_db()
    c.execute("INSERT OR IGNORE INTO channels (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def remove_channel(username):
    conn, c = get_db()
    c.execute("DELETE FROM channels WHERE username = ?", (username,))
    conn.commit()
    conn.close()
  
