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
    c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, link TEXT, count INTEGER, remaining INTEGER, cost INTEGER, status TEXT DEFAULT 'active')''')
    c.execute('''CREATE TABLE IF NOT EXISTS order_history (user_id INTEGER, order_id INTEGER, PRIMARY KEY(user_id, order_id))''')
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

def create_gift_db(code, points, max_uses):
    conn, c = get_db()
    c.execute("INSERT INTO gifts (code, points, max_uses) VALUES (?, ?, ?)", (code, points, max_uses))
    conn.commit()
    conn.close()

def redeem_gift_db(user_id, code):
    conn, c = get_db()
    c.execute("SELECT * FROM gift_history WHERE user_id = ? AND code = ?", (user_id, code))
    if c.fetchone():
        conn.close()
        return "already_redeemed"
    
    c.execute("SELECT points, max_uses, current_uses FROM gifts WHERE code = ?", (code,))
    gift = c.fetchone()
    if not gift:
        conn.close()
        return "invalid"
    
    pts, max_u, curr_u = gift
    if curr_u >= max_u:
        conn.close()
        return "expired"
    
    c.execute("UPDATE gifts SET current_uses = current_uses + 1 WHERE code = ?", (code,))
    c.execute("INSERT INTO gift_history (user_id, code) VALUES (?, ?)", (user_id, code))
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (pts, user_id))
    conn.commit()
    conn.close()
    return pts

def add_order(user_id, link, count, cost):
    conn, c = get_db()
    c.execute("INSERT INTO orders (user_id, link, count, remaining, cost) VALUES (?, ?, ?, ?, ?)", (user_id, link, count, count, cost))
    conn.commit()
    conn.close()

def get_active_order(user_id):
    conn, c = get_db()
    c.execute('''SELECT id, link FROM orders 
                 WHERE remaining > 0 AND status = 'active' AND user_id != ? 
                 AND id NOT IN (SELECT order_id FROM order_history WHERE user_id = ?) LIMIT 1''', (user_id, user_id))
    res = c.fetchone()
    conn.close()
    return res

def get_order_link_db(order_id):
    conn, c = get_db()
    c.execute("SELECT link FROM orders WHERE id = ?", (order_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def complete_task(user_id, order_id):
    conn, c = get_db()
    c.execute("SELECT * FROM order_history WHERE user_id = ? AND order_id = ?", (user_id, order_id))
    if not c.fetchone():
        c.execute("INSERT INTO order_history (user_id, order_id) VALUES (?, ?)", (user_id, order_id))
        c.execute("UPDATE orders SET remaining = remaining - 1 WHERE id = ?", (order_id,))
        c.execute("UPDATE orders SET status = 'completed' WHERE remaining <= 0")
        c.execute("UPDATE users SET points = points + 15 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def skip_order_db(user_id, order_id):
    conn, c = get_db()
    c.execute("INSERT OR IGNORE INTO order_history (user_id, order_id) VALUES (?, ?)", (user_id, order_id))
    conn.commit()
    conn.close()
    
