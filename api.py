from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, hmac, hashlib, time, os

app = Flask(__name__)
CORS(app)
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
DB = 'kapibara.db'
MAX_PER_HOUR = 200000

def get_db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with get_db() as conn:
        conn.executescript("""
          CREATE TABLE IF NOT EXISTS scores(
            user_id INTEGER PRIMARY KEY,
            name    TEXT,
            score   INTEGER DEFAULT 0,
            ts      INTEGER DEFAULT 0
          );
          CREATE TABLE IF NOT EXISTS referrals(
            user_id     INTEGER PRIMARY KEY,
            referred_by INTEGER,
            ts          INTEGER
          );
        """)

@app.route('/health')
def health():
    return jsonify(ok=True, ts=int(time.time()))

@app.route('/leaderboard')
def leaderboard():
    with get_db() as conn:
        rows = conn.execute(
            'SELECT user_id, name, score FROM scores ORDER BY score DESC LIMIT 100'
        ).fetchall()
    return jsonify(leaders=[dict(r) for r in rows])

@app.route('/score', methods=['POST'])
def score():
    d = request.json or {}
    uid   = int(d.get('user_id', 0))
    name  = str(d.get('name', 'Игрок'))[:40]
    score = int(d.get('score', 0))
    if not uid:
        return jsonify(ok=False)
    with get_db() as conn:
        row = conn.execute(
            'SELECT score, ts FROM scores WHERE user_id=?', (uid,)
        ).fetchone()
        if row:
            elapsed_h = max(0.1, (time.time() - row['ts']) / 3600)
            cap = row['score'] + MAX_PER_HOUR * elapsed_h
            score = min(score, int(cap))
        conn.execute(
            'INSERT INTO scores(user_id, name, score, ts) VALUES(?,?,?,?) '
            'ON CONFLICT(user_id) DO UPDATE SET '
            'name=excluded.name, '
            'score=MAX(score, excluded.score), '
            'ts=excluded.ts',
            (uid, name, score, int(time.time()))
        )
    return jsonify(ok=True)

@app.route('/referral', methods=['POST'])
def referral():
    d = request.json or {}
    uid = int(d.get('user_id', 0))
    ref = int(d.get('referred_by', 0))
    if not uid or not ref or uid == ref:
        return jsonify(ok=False)
    with get_db() as conn:
        if conn.execute(
            'SELECT 1 FROM referrals WHERE user_id=?', (uid,)
        ).fetchone():
            return jsonify(ok=False, reason='duplicate')
        conn.execute(
            'INSERT INTO referrals(user_id, referred_by, ts) VALUES(?,?,?)',
            (uid, ref, int(time.time()))
        )
        conn.execute(
            'UPDATE scores SET score=score+500 WHERE user_id=?', (ref,)
        )
    return jsonify(ok=True)

@app.route('/notify/register', methods=['POST'])
def notify_register():
    d = request.json or {}
    uid     = int(d.get('user_id', 0))
    chat_id = int(d.get('chat_id', 0))
    enabled = bool(d.get('enabled', True))
    if not uid or not chat_id:
        return jsonify(ok=False)
    with get_db() as conn:
        conn.executescript("""
          CREATE TABLE IF NOT EXISTS notifications(
            user_id   INTEGER PRIMARY KEY,
            chat_id   INTEGER,
            enabled   INTEGER DEFAULT 1,
            last_sent INTEGER DEFAULT 0
          );
        """)
        conn.execute(
            'INSERT INTO notifications(user_id,chat_id,enabled,last_sent) VALUES(?,?,?,0) '
            'ON CONFLICT(user_id) DO UPDATE SET chat_id=excluded.chat_id, enabled=excluded.enabled',
            (uid, chat_id, 1 if enabled else 0)
        )
    return jsonify(ok=True)

@app.route('/notify/pending')
def notify_pending():
    with get_db() as conn:
        try:
            rows = conn.execute(
                'SELECT user_id, chat_id FROM notifications '
                'WHERE enabled=1 AND (? - last_sent) > 14400',
                (int(time.time()),)
            ).fetchall()
        except:
            rows = []
    return jsonify(users=[dict(r) for r in rows])

@app.route('/notify/sent', methods=['POST'])
def notify_sent():
    d = request.json or {}
    uid = int(d.get('user_id', 0))
    with get_db() as conn:
        try:
            conn.execute(
                'UPDATE notifications SET last_sent=? WHERE user_id=?',
                (int(time.time()), uid)
            )
        except:
            pass
    return jsonify(ok=True)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
