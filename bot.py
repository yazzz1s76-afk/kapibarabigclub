import os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN  = os.environ['BOT_TOKEN']
WEBAPP_URL = 'https://kapibarabigclub.pages.dev'

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = ctx.args
    ref  = args[0] if args else ''

    # Реферальная ссылка
    if ref.startswith('ref_'):
        ref_id = ref.replace('ref_', '')
        logging.info(f'Реферал: {user.id} пришёл от {ref_id}')

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text='🦫 Играть',
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]])

    await update.message.reply_text(
        f'Привет, {user.first_name}! 👋\n\n'
        '🦫 Добро пожаловать в <b>Капибара Клуб</b>!\n\n'
        '🥕 Корми Васю\n'
        '📈 Прокачивай улучшения\n'
        '🏆 Стань легендой в рейтинге\n\n'
        'Нажми кнопку ниже чтобы начать:',
        parse_mode='HTML',
        reply_markup=keyboard
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🦫 <b>Капибара Клуб — помощь</b>\n\n'
        '🥕 Тапай на Васю — получай морковки\n'
        '⚡ Следи за аппетитом — восстанавливается сам\n'
        '🍖 Корми Васю — сытость падает если не играть\n'
        '🛒 Покупай улучшения в магазине\n'
        '👥 Приглашай друзей — +500 морковок за каждого\n\n'
        '/start — начать игру',
        parse_mode='HTML'
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help',  help_cmd))
    logging.info('Бот запущен!')
    app.run_polling()
