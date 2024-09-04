import telebot
import os
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(API_TOKEN)

teams = [
    {"number": "1️⃣", "captain": "@pashukt", "members": ["@alex", "@oleg"]},
    {"number": "2️⃣", "captain": "", "members": []},
    {"number": "3️⃣", "captain": "@dog", "members": ["@pozwr", "@lada"]},
    {"number": "4️⃣", "captain": "", "members": []},
    {"number": "5️⃣", "captain": "", "members": []},
    {"number": "6️⃣", "captain": "", "members": []},
    {"number": "7️⃣", "captain": "", "members": []},
    {"number": "8️⃣", "captain": "@frj", "members": []}
]

message_ids = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    for i, team in enumerate(teams):
        team_name = f"{team['number']} Команда: {team['captain']}" if team['captain'] else f"{team['number']} Пустая команда"
        markup.add(InlineKeyboardButton(team_name, callback_data=f"team{i+1}"))
    sent_message = bot.send_message(message.chat.id, "Выбери команду: ", reply_markup=markup)
    message_ids[message.chat.id] = sent_message.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith('team'))
def handle_team_selection(call):
    team_number = int(call.data.replace('team', '')) - 1
    team = teams[team_number]
    if team['members']:
        members_list = "\n".join([f"{i+1}. {member}" for i, member in enumerate(team['members'])])
    else:
        members_list = "Пусто🤷‍♂️"
    team_members_message = f"{team['number']} Команда:\n{members_list}"
    bot.answer_callback_query(call.id, team_members_message)
    bot.send_message(call.message.chat.id, team_members_message)
    if call.message.chat.id in message_ids:
        bot.delete_message(call.message.chat.id, message_ids[call.message.chat.id])
        del message_ids[call.message.chat.id]

bot.infinity_polling()
