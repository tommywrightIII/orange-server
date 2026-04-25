from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'orange_admin_secret')

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
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
    conn.commit()
    cur.close()
    conn.close()

init_db()

def check_admin(req):
    token = req.headers.get('X-Admin-Token') or req.args.get('token')
    return token == ADMIN_TOKEN

@app.route('/api/items', methods=['GET'])
def get_items():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM items ORDER BY created_at DESC')
    items = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for item in items:
        d = dict(item)
        d['photos'] = json.loads(d['photos'] or '[]')
        result.append(d)
    return jsonify(result)

@app.route('/api/items', methods=['POST'])
def add_item():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    photos = json.dumps(data.get('photos', []))
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO items (brand,name,cat,size,price,price_usd,cond,desc,emoji,photos,sold) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',
        (data['brand'], data['name'], data['cat'], data['size'],
         data['price'], data.get('priceUsd', 0), data['cond'],
         data.get('desc', ''), data.get('emoji', '📦'), photos, 0)
    )
    item_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'id': item_id, 'ok': True})

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    photos = json.dumps(data.get('photos', []))
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'UPDATE items SET brand=%s,name=%s,cat=%s,size=%s,price=%s,price_usd=%s,cond=%s,desc=%s,emoji=%s,photos=%s,sold=%s WHERE id=%s',
        (data['brand'], data['name'], data['cat'], data['size'],
         data['price'], data.get('priceUsd', 0), data['cond'],
         data.get('desc', ''), data.get('emoji', '📦'), photos,
         data.get('sold', 0), item_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM items WHERE id=%s', (item_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/items/<int:item_id>/toggle', methods=['PATCH'])
def toggle_sold(item_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE items SET sold = 1 - sold WHERE id=%s', (item_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
