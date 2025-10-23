from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_random_key"

DB_PATH = "db.sqlite3"
DATA_CSV = Path("data/woman_risk_for_frontend.csv")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            mobile TEXT UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def load_data_as_json(limit=None):
    if not DATA_CSV.exists():
        return []
    df = pd.read_csv(DATA_CSV)
    cols = [c for c in ['id','state','city','place_type','latitude','longitude','zone','risk_score','last_updated','source','dynamic_zone'] if c in df.columns]
    df = df[cols]
    if limit:
        df = df.head(limit)
    return df.to_dict(orient='records')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/data')
def data_api():
    try:
        data = load_data_as_json()
        return jsonify({"status":"ok","data": data})
    except Exception as e:
        return jsonify({"status":"error","message": str(e)}), 500

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        mobile = request.form['mobile']
        pwd = request.form['password']
        pwd_hash = generate_password_hash(pwd)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (name, age, gender, mobile, password_hash) VALUES (?,?,?,?,?)',
                      (name, age, gender, mobile, pwd_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Mobile already used", 400
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        mobile = request.form['mobile']
        pwd = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, password_hash FROM users WHERE mobile=?', (mobile,))
        row = c.fetchone()
        conn.close()
        if not row:
            return "Invalid credentials", 401
        uid, pwd_hash = row
        if check_password_hash(pwd_hash, pwd):
            session['user_id'] = uid
            return redirect(url_for('index'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    import math
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

@app.route('/nearest', methods=['GET'])
def nearest():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    df = pd.read_csv(DATA_CSV)
    df['dist'] = df.apply(lambda r: haversine(lat, lon, r['latitude'], r['longitude']), axis=1)
    nearest = df.sort_values('dist').iloc[0].to_dict()
    return jsonify(nearest)

if __name__ == "__main__":
    app.run(debug=True)
