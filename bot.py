import os, json, urllib.request, time, threading

TOKEN    = os.environ['BOT_TOKEN']
APP_URL  = 'https://kapibarabigclub.pages.dev'
API      = f'https://api.telegram.org/bot{TOKEN}'
BACKEND  = 'https://kapibarabigclub.onrender.com'
YOUR_ID  = 235364213
OFFSET   = 0

NOTIF_MESSAGES = [
    '🦫 Вася скучает! Он уже давно не ел морковку...',
    '😢 Вася голодает! Зайди покорми его!',
    '🥕 Морковки сами себя не соберут! Вася ждёт тебя.',
    '🦫 Эй! Вася смотрит на тебя грустными глазами...',
    '⚡ Аппетит Васи полный! Самое время потапать.',
]

def api_call(method, data):
    req = urllib.request.Request(
        f'{API}/{method}',
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'API error {method}: {e}')
        return {}

def backend_get(path):
    try:
        with urllib.request.urlopen(f'{BACKEND}{path}', timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'Backend GET error {path}: {e}')
        return {}

def backend_post(path, data):
    try:
        req = urllib.request.Request(
            f'{BACKEND}{path}',
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'Backend POST error {path}: {e}')
        return {}

def send(chat_id, text, keyboard=None):
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if keyboard:
        data['reply_markup'] = json.dumps(keyboard)
    return api_call('sendMessage', data)

def get_invoice_links(chat_id):
    products = [
        ('⚡ Полный заряд аппетита', 'Восстановить всю энергию Васи мгновенно', 'energy_refill', 50),
        ('🥕×2 Двойной доход',       'Двойной доход от тапов на 1 час',          'double_tap',    100),
        ('🚀 Стартовый пак',         '+5000 морковок сразу на счёт',              'starter_pack',  200),
        ('🏅 Золотая Вася',          'Уникальный золотой скин навсегда',          'gold_skin',     500),
    ]
    results = []
    for title, desc, payload, amount in products:
        data = {
            'chat_id': chat_id,
            'title': title,
            'description': desc,
            'payload': payload,
            'currency': 'XTR',
            'prices': [{'label': title, 'amount': amount}]
        }
        result = api_call('createInvoiceLink', data)
        link = result.get('result', 'ОШИБКА')
        results.append(f'<b>{payload}:</b>\n{link}')
    return results

def handle(msg):
    if 'text' not in msg:
        return
    chat_id = msg['chat']['id']
    text    = msg['text']
    name    = msg.get('from', {}).get('first_name', 'друг')
    user_id = msg.get('from', {}).get('id', 0)

    if text == '/getlinks':
        if user_id != YOUR_ID:
            send(chat_id, '❌ Нет доступа')
            return
        send(chat_id, '⏳ Создаю ссылки...')
        links = get_invoice_links(chat_id)
        send(chat_id, '✅ Инвойс-ссылки:\n\n' + '\n\n'.join(links))
        return

    if text.startswith('/start'):
        keyboard = {'inline_keyboard': [[{
            'text': '🦫 Играть',
            'web_app': {'url': APP_URL}
        }]]}
        send(chat_id,
            f'Привет, {name}! 👋\n\n'
            '🦫 Добро пожаловать в <b>Капибара Клуб</b>!\n\n'
            '🥕 Корми Васю\n'
            '📈 Прокачивай улучшения\n'
            '🏆 Стань легендой в рейтинге\n\n'
            'Нажми кнопку ниже чтобы начать:',
            keyboard
        )
        return

    if text.startswith('/help'):
        send(chat_id,
            '🦫 <b>Помощь</b>\n\n'
            '🥕 Тапай на Васю — получай морковки\n'
            '⚡ Аппетит тратится на тапы, восстанавливается сам\n'
            '🍖 Сытость падает если не играть\n'
            '🛒 Покупай улучшения в магазине\n'
            '👥 Приглашай друзей — +500 морковок\n\n'
            '/start — начать игру'
        )

def send_notifications():
    while True:
        try:
            data = backend_get('/notify/pending')
            users = data.get('users', [])
            print(f'Уведомления: {len(users)} пользователей')
            for i, u in enumerate(users):
                msg = NOTIF_MESSAGES[i % len(NOTIF_MESSAGES)]
                keyboard = {'inline_keyboard': [[{
                    'text': '🦫 Покормить Васю!',
                    'web_app': {'url': APP_URL}
                }]]}
                result = send(u['chat_id'], msg, keyboard)
                if result.get('ok'):
                    backend_post('/notify/sent', {'user_id': u['user_id']})
                time.sleep(0.3)
        except Exception as e:
            print(f'Ошибка уведомлений: {e}')
        time.sleep(1800)

def main():
    global OFFSET
    print('Бот запущен!')
    t = threading.Thread(target=send_notifications, daemon=True)
    t.start()
    while True:
        try:
            resp = api_call('getUpdates', {
                'offset': OFFSET,
                'timeout': 30,
                'allowed_updates': ['message']
            })
            for upd in resp.get('result', []):
                OFFSET = upd['update_id'] + 1
                if 'message' in upd:
                    handle(upd['message'])
        except Exception as e:
            print(f'Ошибка: {e}')
            time.sleep(5)

if __name__ == '__main__':
    main()
