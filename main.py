import telebot
import os
import sqlite3
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

# Constants
TEAM_COUNT = 8
MAX_TEAM_SIZE = 5
BACK_BUTTON_TEXT = "🔙 Назад"
JOIN_TEAM_TEXT = "👥 Присоедениться к команде"
VIEW_TEAMS_TEXT = "👀 Посмотреть список всех команд"
MY_TEAM_TEXT = "🧑‍💻 Моя команда"
NO_TEAM_MESSAGE = "У вас пока нету команды!"
ALREADY_IN_TEAM_MESSAGE = "Вы уже в одной из команд!"
CANCEL_JOIN_TEAM_MESSAGE = "⛔ Нет, вернуться назад"
JOIN_TEAM_CONFIRMATION_MESSAGE = "👌 Да, присоедениться к команде"

def get_users():
    """Fetches users from the database and returns them as a list of dictionaries."""
    with sqlite3.connect('users.db') as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users ORDER BY team_number, is_captain DESC')
        return [
            {"id": row[0], "user_id": row[1], "user_name": row[2], "team_number": row[3], "is_captain": row[4]}
            for row in cursor.fetchall()
        ]

def get_teams(users):
    """Organizes users into teams."""
    teams = {i: [] for i in range(1, TEAM_COUNT + 1)}
    for user in users:
        teams[user['team_number']].append(user)
    return teams

def generate_main_menu():
    """Generates the main menu keyboard."""
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    reply_markup.add(KeyboardButton(JOIN_TEAM_TEXT), KeyboardButton(VIEW_TEAMS_TEXT), KeyboardButton(MY_TEAM_TEXT))
    return reply_markup

def generate_team_selection_keyboard(teams):
    """Generates a keyboard for team selection."""
    markup = InlineKeyboardMarkup()
    for i in range(1, TEAM_COUNT + 1):
        team_preview = f"{i}\uFE0F\u20E3 Команда: {next((user['user_name'] for user in teams[i] if user['is_captain']), 'пусто')}"
        markup.add(InlineKeyboardButton(team_preview, callback_data=f"team{i}"))
    markup.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back"))
    return markup

def choose_action(message):
    """Displays the main menu."""
    bot.send_message(message.chat.id, "📍 Главное меню:", reply_markup=generate_main_menu())

def is_user_in_team(users, user_id):
    """Checks if the user is already in a team."""
    return any(user['user_id'] == user_id for user in users)

def add_user_to_db(new_user):
    """Adds a new user to the database."""
    with sqlite3.connect('users.db') as connection:
        cursor = connection.cursor()
        cursor.execute('INSERT INTO users (user_id, user_name, team_number, is_captain) VALUES (?, ?, ?, ?)',
                       (new_user['user_id'], new_user['user_name'], new_user['team_number'], new_user['is_captain']))
        connection.commit()

users = get_users()
teams = get_teams(users)

@bot.message_handler(commands=['start'])
def handle_start(message):
    choose_action(message)

@bot.message_handler(func=lambda message: message.text == JOIN_TEAM_TEXT)
def join_teams_lead(message):
    if is_user_in_team(users, message.from_user.id):
        bot.send_message(message.chat.id, ALREADY_IN_TEAM_MESSAGE)
        choose_action(message)
    else:
        bot.send_message(message.chat.id, "👇 Выберите команду:", reply_markup=generate_team_selection_keyboard(teams))

@bot.message_handler(func=lambda message: message.text == VIEW_TEAMS_TEXT)
def view_teams(message):
    teams_list = "\n\n".join(
        f"{i}\uFE0F\u20E3 Команда:\n" +
        ("\n".join(f"{u}. {user['user_name']}" for u, user in enumerate(teams[i], start=1)) or "Пусто 🤷‍♂️")
        for i in range(1, TEAM_COUNT + 1))
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back"))
    bot.send_message(message.chat.id, teams_list, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == MY_TEAM_TEXT)
def my_team(message):
    if not is_user_in_team(users, message.from_user.id):
        bot.send_message(message.chat.id, NO_TEAM_MESSAGE)
        choose_action(message)
        return
    current_team_number = next(user['team_number'] for user in users if user['user_id'] == message.from_user.id)
    members_list = "\n".join(f"{i}. {user['user_name']}" for i, user in enumerate(teams[current_team_number], start=1)) or "Пусто 🤷‍♂️"
    team_members_message = f"{current_team_number}\uFE0F\u20E3 Команда:\n{members_list}"
    bot.send_message(message.chat.id, team_members_message)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def handle_back_callback(call):
    choose_action(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('team'))
def handle_team_selection(call):
    current_team_number = int(call.data.replace('team', ''))
    members_list = "\n".join(f"{i}. {user['user_name']}" for i, user in enumerate(teams[current_team_number], start=1)) or "Пусто 🤷‍♂️"
    team_members_message = f"{current_team_number}\uFE0F\u20E3 Команда:\n{members_list} \n\nВы действительно хотите присоедниться к команде?"
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    reply_markup.add(KeyboardButton(f"{JOIN_TEAM_CONFIRMATION_MESSAGE} {current_team_number}\uFE0F\u20E3!"), KeyboardButton(CANCEL_JOIN_TEAM_MESSAGE))
    bot.answer_callback_query(call.id, team_members_message)
    bot.send_message(call.message.chat.id, team_members_message, reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text == CANCEL_JOIN_TEAM_MESSAGE)
def handle_back_callback(message):
    join_teams_lead(message)

@bot.message_handler(func=lambda message: message.text.startswith(JOIN_TEAM_CONFIRMATION_MESSAGE))
def join_team(message):
    current_team_number = int(message.text.split()[-1][0])
    if len(teams[current_team_number]) >= MAX_TEAM_SIZE:
        bot.send_message(message.chat.id, f"К сожалению, команда {current_team_number}\uFE0F\u20E3 уже полна (максимум {MAX_TEAM_SIZE} участников). Выберите другую команду:")
        join_teams_lead(message)
        return
    user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name}"
    new_user = {
        "id": None,
        "user_id": message.from_user.id,
        "user_name": user_name,
        "team_number": current_team_number,
        "is_captain": 1 if not teams[current_team_number] else 0
    }
    users.append(new_user)
    teams[current_team_number].append(new_user)
    add_user_to_db(new_user)
    bot.send_message(message.chat.id, f"Вы успешно присоединились к команде {current_team_number}\uFE0F\u20E3!")
    if new_user['is_captain'] == 1:
        bot.send_message(message.chat.id, f"Вы являетесь капитаном в команде {current_team_number}\uFE0F\u20E3!")
    choose_action(message)

bot.infinity_polling()
