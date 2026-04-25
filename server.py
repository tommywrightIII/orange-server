from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)

DB_PATH = 'items.db'
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'orange_admin_secret')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            cat TEXT NOT NULL,
            size TEXT NOT NULL,
            price INTEGER NOT NULL,
            price_usd INTEGER DEFAULT 0,
            cond INTEGER NOT NULL,
            desc TEXT,
            emoji TEXT DEFAULT '📦',
            photos TEXT DEFAULT '[]',
            sold INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Add demo items if empty
    count = conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    if count == 0:
        demo = [
            ('Nike', 'Air Force 1 Low', 'shoes', '42', 11500, 0, 8, 'Куплены год назад, носились редко. Небольшая потёртость на носке.', '👟', '[]', 0),
            ('Adidas', 'Yeezy Boost 350', 'shoes', '41', 24000, 0, 9, 'В отличном состоянии, одевали раза 4.', '👟', '[]', 0),
            ('Supreme', 'Box Logo Tee', 'clothes', 'L', 15000, 0, 10, 'Ни разу не одевалась. Куплена на дропе.', '👕', '[]', 0),
        ]
        conn.executemany('INSERT INTO items (brand,name,cat,size,price,price_usd,cond,desc,emoji,photos,sold) VALUES (?,?,?,?,?,?,?,?,?,?,?)', demo)
    conn.commit()
    conn.close()

def check_admin(req):
    token = req.headers.get('X-Admin-Token') or req.args.get('token')
    return token == ADMIN_TOKEN

# ── GET all items ──
@app.route('/api/items', methods=['GET'])
def get_items():
    conn = get_db()
    items = conn.execute('SELECT * FROM items ORDER BY created_at DESC').fetchall()
    conn.close()
    result = []
    for item in items:
        d = dict(item)
        d['photos'] = json.loads(d['photos'] or '[]')
        result.append(d)
    return jsonify(result)

# ── POST add item ──
@app.route('/api/items', methods=['POST'])
def add_item():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    photos = json.dumps(data.get('photos', []))
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO items (brand,name,cat,size,price,price_usd,cond,desc,emoji,photos,sold) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (data['brand'], data['name'], data['cat'], data['size'],
         data['price'], data.get('priceUsd', 0), data['cond'],
         data.get('desc', ''), data.get('emoji', '📦'), photos, 0)
    )
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': item_id, 'ok': True})

# ── PUT update item ──
@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    photos = json.dumps(data.get('photos', []))
    conn = get_db()
    conn.execute(
        'UPDATE items SET brand=?,name=?,cat=?,size=?,price=?,price_usd=?,cond=?,desc=?,emoji=?,photos=?,sold=? WHERE id=?',
        (data['brand'], data['name'], data['cat'], data['size'],
         data['price'], data.get('priceUsd', 0), data['cond'],
         data.get('desc', ''), data.get('emoji', '📦'), photos,
         data.get('sold', 0), item_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── DELETE item ──
@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    conn.execute('DELETE FROM items WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── PATCH toggle sold ──
@app.route('/api/items/<int:item_id>/toggle', methods=['PATCH'])
def toggle_sold(item_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    conn.execute('UPDATE items SET sold = 1 - sold WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
