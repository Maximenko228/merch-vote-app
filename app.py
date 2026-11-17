import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'super_secret_merch_key_mgri'

ADMIN_CREDENTIALS = {
    "admin": "mgri2026"
}

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS merch (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image TEXT NOT NULL,
            likes INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merch_id INTEGER NOT NULL,
            client_id TEXT NOT NULL,
            FOREIGN KEY (merch_id) REFERENCES merch (id)
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM merch')
    if cursor.fetchone()[0] == 0:
        default_items = [
            ('Блокнот с енотом', 'Фирменный блокнот МГРИ на спирали с персонажем-енотом', '/static/images/blocnot.jpg'),
            ('Блокнот с корпусом МГРИ', 'Стильный блокнот с иллюстрацией здания университета', '/static/images/bloknotkoll.jpg'),
            ('Черная футболка МГРИ', 'Классическая черная оверсайз футболка с принтом', '/static/images/futbolkaB.jpg'),
            ('Белая футболка МГРИ', 'Классическая белая оверсайз футболка с принтом', '/static/images/futbolkaW.jpg'),
            ('Черное худи МГРИ', 'Теплое черное худи с енотом и логотипом', '/static/images/hoodieB.jpg'),
            ('Белое худи МГРИ', 'Уютное белое худи с принтом енотом', '/static/images/hoodieW.jpg')
        ]
        cursor.executemany('INSERT INTO merch (title, description, image) VALUES (?, ?, ?)', default_items)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM merch').fetchall()
    conn.close()
    return render_template('index.html', items=items)

@app.route('/favorite/<int:merch_id>', methods=['POST'])
def add_favorite(merch_id):
    client_id = request.form.get('client_id')
    if not client_id:
        return jsonify({'status': 'error', 'message': 'client_id missing'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE merch SET likes = likes + 1 WHERE id = ?', (merch_id,))
    conn.execute('INSERT INTO favorites (merch_id, client_id) VALUES (?, ?)', (merch_id, client_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/reset', methods=['POST'])
def reset_session():
    client_id = request.form.get('client_id')
    if not client_id:
        return jsonify({'status': 'error', 'message': 'client_id missing'}), 400

    conn = get_db_connection()
    old_favs = conn.execute('SELECT merch_id FROM favorites WHERE client_id = ?', (client_id,)).fetchall()
    
    for fav in old_favs:
        conn.execute('UPDATE merch SET likes = likes - 1 WHERE id = ?', (fav['merch_id'],))
        
    conn.execute('DELETE FROM favorites WHERE client_id = ?', (client_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/favorites')
def favorites():
    client_id = request.args.get('client_id')
    conn = get_db_connection()
    if client_id:
        favs = conn.execute('''
            SELECT merch.title, merch.description, merch.image 
            FROM favorites 
            JOIN merch ON favorites.merch_id = merch.id 
            WHERE favorites.client_id = ?
        ''', (client_id,)).fetchall()
    else:
        favs = []
    conn.close()
    return render_template('favorites.html', items=favs)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            session['logged_in'] = True
            return redirect(url_for('stats'))
        else:
            error = 'Неверный логин или пароль!'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/stats')
def stats():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
        
    conn = get_db_connection()
    stats_data = conn.execute('SELECT title, likes, image FROM merch ORDER BY likes DESC').fetchall()
    total_users = conn.execute('SELECT COUNT(DISTINCT client_id) FROM favorites').fetchone()[0]
    conn.close()
    return render_template('stats.html', items=stats_data, total_users=total_users)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)