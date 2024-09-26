import telebot
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from src.config import *

bot = telebot.TeleBot(API_TOKEN)

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
    teams = {i: [] for i in range(1, 9)}
    for user in users:
        teams[user['team_number']].append(user)
    return teams

def generate_main_menu():
    """Generates the main menu keyboard."""
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reply_markup.add(KeyboardButton(JOIN_TEAM_BUTTON_TEXT), KeyboardButton(VIEW_TEAMS_BUTTON_TEXT), KeyboardButton(MY_TEAM_BUTTON_TEXT))
    return reply_markup

def generate_team_selection_keyboard(teams):
    """Generates a keyboard for team selection."""
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    for i in range(1, 9):
        team_preview = f"{i}\uFE0F\u20E3 Команда: {next((user['user_name'] for user in teams[i] if user['is_captain']), 'пусто')}"
        reply_markup.add(KeyboardButton(team_preview))
    reply_markup.add(KeyboardButton(BACK_BUTTON_TEXT))
    return reply_markup

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
    update_users()

def delete_user_from_db(user):
    """Remove a user from the database."""
    with sqlite3.connect('users.db') as connection:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user['user_id'],))
        connection.commit()
    update_users()

def set_new_captain(user):
    """Set a user['is_captain'] to 1 and update the database."""
    with sqlite3.connect('users.db') as connection:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE users
            SET is_captain = ?
            WHERE user_id = ?;
            """, (1, user['user_id']))
        connection.commit()

def create_emoji_number(number):
    """Create emoji from number"""
    return str(number) + "\uFE0F\u20E3"

def update_users():
    """Update user database"""
    global users, teams
    users = get_users()
    teams = get_teams(users)

users = get_users()
teams = get_teams(users)

@bot.message_handler(commands=['start'])
def handle_start(message):
    choose_action(message)

@bot.message_handler(func=lambda message: message.text == JOIN_TEAM_BUTTON_TEXT)
def preview_teams_with_lead(message):
    if is_user_in_team(users, message.from_user.id):
        bot.send_message(message.chat.id, ALREADY_IN_TEAM_MESSAGE)
        choose_action(message)
    else:
        bot.send_message(message.chat.id, CHOOSE_TEAM_ACTION_MESSAGE, reply_markup=generate_team_selection_keyboard(teams))

@bot.message_handler(func=lambda message: message.text == VIEW_TEAMS_BUTTON_TEXT)
def view_teams(message):
    teams_list = "\n\n".join(
        f"{create_emoji_number(i)} Команда:\n" +
        ("\n".join(f"{u}. {user['user_name']}" for u, user in enumerate(teams[i], start=1)) or EMPTY_TEAM_MESSAGE)
        for i in range(1, 9))
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reply_markup.add(KeyboardButton(BACK_BUTTON_TEXT))
    bot.send_message(message.chat.id, teams_list, reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text == MY_TEAM_BUTTON_TEXT)
def my_team(message):
    if not is_user_in_team(users, message.from_user.id):
        bot.send_message(message.chat.id, NO_TEAM_MESSAGE)
        choose_action(message)
        return
    current_team_number = next(user['team_number'] for user in users if user['user_id'] == message.from_user.id)
    members_list = "\n".join(f"{i}. {user['user_name']}" for i, user in enumerate(teams[current_team_number], start=1))
    team_members_message = f"{create_emoji_number(current_team_number)} Команда:\n{members_list}"
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if any(user['is_captain'] for user in users if user['user_id'] == message.from_user.id) and len(teams[current_team_number]) > 1:
        reply_markup.add(KeyboardButton(DELETE_TEAM_MEMBERS_BUTTON_TEXT))
    reply_markup.add(KeyboardButton(LEAVE_TEAM_BUTTON_TEXT), KeyboardButton(BACK_BUTTON_TEXT))
    bot.send_message(message.chat.id, team_members_message, reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text == BACK_BUTTON_TEXT)
def handle_back(message):
    choose_action(message)

@bot.message_handler(func=lambda message: message.text.startswith(LEAVE_TEAM_BUTTON_TEXT))
def leave_team_confirmation(message):
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reply_markup.add(KeyboardButton(LEAVE_TEAM_CONFIRMATION_BUTTON_TEXT), KeyboardButton(CANCEL_LEAVE_TEAM_BUTTON_TEXT))
    bot.send_message(message.chat.id, LEAVE_TEAM_CONFIRMATION_MESSAGE, reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text == LEAVE_TEAM_CONFIRMATION_BUTTON_TEXT)
def leave_team(message):
    user = next(user for user in users if user['user_id'] == message.from_user.id)
    if user['is_captain'] != 1:
        delete_user_from_db(user)
    else:
        if len(teams[user['team_number']]) == 1:
            delete_user_from_db(user)
        else:
            set_new_captain(teams[user['team_number']][1])
            bot.send_message(teams[user['team_number']][1]['user_id'], f"{BE_CAPTAIN_MESSAGE} {create_emoji_number(user['team_number'])}!")
            delete_user_from_db(user)
    bot.send_message(message.chat.id, LEAVE_TEAM_SUCCESS_MESSAGE, reply_markup=generate_main_menu())

@bot.message_handler(func=lambda message: message.text == DELETE_TEAM_MEMBERS_BUTTON_TEXT)
def delete_team_member_menu(message):
    current_team_number = next(user['team_number'] for user in users if user['user_id'] == message.from_user.id)
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reply_markup.add(*[KeyboardButton(f"✏️ Удалить: {user['user_name']}") for user in teams[current_team_number] if user['user_id'] != message.from_user.id])
    reply_markup.add(KeyboardButton(CANCEL_DELETE_TEAM_MEMBERS_BUTTON_TEXT))
    bot.send_message(message.chat.id, DELETE_TEAM_MEMBER_MESSAGE, reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text.startswith(DELETE_TEAM_MEMBER_START_BUTTON_TEXT))
def delete_team_member_confirmation(message):
    user_name_to_delete = message.text[len(DELETE_TEAM_MEMBER_START_BUTTON_TEXT):]
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reply_markup.add(KeyboardButton(f"{DELETE_TEAM_MEMBER_BUTTON_TEXT}{user_name_to_delete}"), KeyboardButton(CANCEL_DELETE_TEAM_MEMBER_BUTTON_TEXT))
    bot.send_message(message.chat.id, f"{DELETE_TEAM_MEMBER_MESSAGE} {user_name_to_delete}", reply_markup=reply_markup)
   
@bot.message_handler(func=lambda message: message.text in [CANCEL_LEAVE_TEAM_BUTTON_TEXT, CANCEL_DELETE_TEAM_MEMBERS_BUTTON_TEXT])
def handle_cancel_leave_team_message(message):
    my_team(message)

@bot.message_handler(func=lambda message: message.text == CANCEL_DELETE_TEAM_MEMBER_BUTTON_TEXT)
def cancel_delete_team_member(message):
    delete_team_member_menu(message)

@bot.message_handler(func=lambda message: message.text.startswith(DELETE_TEAM_MEMBER_BUTTON_TEXT))
def delete_team_member(message):
    user_name_to_delete = message.text[len(DELETE_TEAM_MEMBER_BUTTON_TEXT):]
    user = next(user for user in users if user['user_name'] == user_name_to_delete)
    delete_user_from_db(user)
    bot.send_message(user['user_id'], f"{TEAM_REJECTION_MESSAGE} {create_emoji_number(user['team_number'])}")
    bot.send_message(message.chat.id, f"✅ {user_name_to_delete} {DELETE_TEAM_MEMBER_SUCCESS_MESSAGE}", reply_markup=generate_main_menu())    


@bot.message_handler(func=lambda message: message.text and "Команда:" in message.text)
def handle_team_selection(message):
    current_team_number = int(message.text[0])
    members_list = "\n".join(f"{i}. {user['user_name']}" for i, user in enumerate(teams[current_team_number], start=1)) or EMPTY_TEAM_MESSAGE
    team_members_message = f"{create_emoji_number(current_team_number)} Команда:\n{members_list} \n\n{JOIN_TEAM_CONFIRAMTION_MESSAGE}"
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    reply_markup.add(KeyboardButton(f"{JOIN_TEAM_CONFIRMATION_BUTTON_TEXT} {create_emoji_number(current_team_number)}!"), KeyboardButton(CANCEL_JOIN_TEAM_BUTTON_TEXT))
    bot.send_message(message.chat.id, team_members_message, reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text == CANCEL_JOIN_TEAM_BUTTON_TEXT)
def handle_cancel_join_team_message(message):
    preview_teams_with_lead(message)

@bot.message_handler(func=lambda message: message.text.startswith(JOIN_TEAM_CONFIRMATION_BUTTON_TEXT))
def join_team(message):
    current_team_number = int(message.text[-4])
    if len(teams[current_team_number]) >= 5:
        bot.send_message(message.chat.id, TEAM_IS_FULL_MESSAGE)
        preview_teams_with_lead(message)
        return
    user_name = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.first_name} {message.from_user.last_name}"
    new_user = {
        "id": None,
        "user_id": message.from_user.id,
        "user_name": user_name,
        "team_number": current_team_number,
        "is_captain": 1 if not teams[current_team_number] else 0
    }
    add_user_to_db(new_user)
    bot.send_message(message.chat.id, JOIN_TEAM_MESSAGE)
    if new_user['is_captain'] == 1:
        bot.send_message(message.chat.id, f"{BE_CAPTAIN_MESSAGE} {create_emoji_number(current_team_number)}!")
    choose_action(message)

bot.infinity_polling()