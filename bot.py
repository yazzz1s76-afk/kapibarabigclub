import os, json, urllib.request, urllib.parse

TOKEN    = os.environ['BOT_TOKEN']
APP_URL  = 'https://kapibarabigclub.pages.dev'
API      = f'https://api.telegram.org/bot{TOKEN}'
OFFSET   = 0

def api(method, data):
    req = urllib.request.Request(
        f'{API}/{method}',
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def send(chat_id, text, keyboard=None):
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if keyboard:
        data['reply_markup'] = json.dumps(keyboard)
    api('sendMessage', data)

def handle(msg):
    if 'text' not in msg:
        return
    chat_id = msg['chat']['id']
    text    = msg['text']
    name    = msg.get('from', {}).get('first_name', 'друг')

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
    elif text.startswith('/help'):
        send(chat_id,
            '🦫 <b>Помощь</b>\n\n'
            '🥕 Тапай на Васю — получай морковки\n'
            '⚡ Аппетит тратится на тапы, восстанавливается сам\n'
            '🍖 Сытость падает если не играть\n'
            '🛒 Покупай улучшения в магазине\n'
            '👥 Приглашай друзей — +500 морковок\n\n'
            '/start — начать игру'
        )

def main():
    global OFFSET
    print('Бот запущен!')
    while True:
        try:
            resp = api('getUpdates', {
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

if __name__ == '__main__':
    main()
