from flask import Flask, request, jsonify
import sqlite3, hmac, hashlib, time, os

app = Flask(__name__)
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

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

Нажми **Commit new file**

---

### Файл 2 — `requirements.txt`

Нажми снова **Add file → Create new file**

Имя: `requirements.txt`
```
flask==3.0.3
gunicorn==22.0.0
```

Нажми **Commit new file**

---

### Файл 3 — `Procfile`

Снова **Add file → Create new file**

Имя: `Procfile` (без расширения — именно так!)
```
web: python api.py
```

Нажми **Commit new file**

---

## ШАГ 2 — Деплой на Railway

**2.1** Открой https://railway.app → войди через GitHub

**2.2** Нажми **New Project**

**2.3** Выбери **Deploy from GitHub repo**

**2.4** Выбери `kapibarabigclub`

**2.5** Railway начнёт деплой. Подожди — увидишь статус **Active** с зелёной точкой (1–2 минуты)

---

## ШАГ 3 — Добавляем токен бота

**3.1** Нажми на свой проект в Railway

**3.2** Вкладка **Variables**

**3.3** Нажми **New Variable** и добавь:
```
BOT_TOKEN = 7123456789:AAFxxx...  (твой токен из @BotFather)
```

**3.4** Railway автоматически перезапустится

---

## ШАГ 4 — Получаем адрес и подключаем к игре

**4.1** Вкладка **Settings → Networking → Generate Domain**

Получишь адрес вида:
```
kapibarabigclub-production.up.railway.app
