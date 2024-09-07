import telebot
import os
import sqlite3
import json
import pprint
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(API_TOKEN)

def get_users():
    users = []
    with sqlite3.connect('users.db') as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT * FROM users
            ORDER BY team_number, is_captain DESC
        ''')
        rows = cursor.fetchall()
        users = [
            {
                "id": row[0],
                "user_id": row[1],
                "user_name": row[2],
                "team_number": row[3],
                "is_captain": row[4]
            }
            for row in rows
        ]
    return users

def get_teams(users):
    teams = {i: [] for i in range(1, 9)} 

    for user in users:
        team_number = user['team_number']
        teams[team_number].append(user)  

    return teams


    
users = get_users()
teams = get_teams(users)

@bot.message_handler(commands=['start'])
def choose_action(message):
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    join_team = KeyboardButton("👥 Присоедениться к команде")
    view_teams = KeyboardButton("👀 Посмотреть список всех команд")
    my_team = KeyboardButton("🧑‍💻 Моя команда")
    reply_markup.add(join_team, view_teams, my_team)
    bot.send_message(message.chat.id, "📍 Главное меню: ", reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text in ["👥 Присоедениться к команде", "⛔ Нет, вернуться назад"])
def handle_action(message):
    markup = InlineKeyboardMarkup()
    for i in range(1, 9):
        team_preview = f"{i}\uFE0F\u20E3 Команда: {next((user['user_name'] for user in teams[i] if user['is_captain'] == True), 'пусто')}"
        markup.add(InlineKeyboardButton(team_preview, callback_data=f"team{i}"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.send_message(message.chat.id, "👇 Выберите команду: ", reply_markup=markup)
        

@bot.message_handler(func=lambda message: message.text == "👀 Посмотреть список всех команд")
def view_teams(message):
    teams_list = "\n\n".join(
        f"{i}\uFE0F\u20E3 Команда:\n" +
        ("\n".join(f"{u}. {user['user_name']}" for u, user in enumerate(teams[i], start=1)) or "Пусто 🤷‍♂️")
        for i in range(1, 9))

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.send_message(message.chat.id, teams_list, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def choose_action_callback(call):
    choose_action(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('team'))
def handle_team_selection(call):
    current_team_number = int(call.data.replace('team', ''))
    members_list = "\n".join(f"{i}. {user['user_name']}" for i, user in enumerate(teams[current_team_number], start=1)) or "Пусто 🤷‍♂️"
    team_members_message = f"{current_team_number}\uFE0F\u20E3 Команда:\n{members_list} \n\nВы действительно хотите присоедниться к команде?"
    reply_markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    join_team = KeyboardButton(f"👌 Да, присоедениться к команде {current_team_number}\uFE0F\u20E3!")
    view_teams = KeyboardButton("⛔ Нет, вернуться назад")
    reply_markup.add(join_team, view_teams)
    bot.answer_callback_query(call.id, team_members_message)
    bot.send_message(call.message.chat.id, team_members_message, reply_markup=reply_markup)

@bot.message_handler(func=lambda message: message.text == "👌 Да, присоедениться!")
def join_team(message):
    # current_team_number = 
    if message.from_user.username:
        user = "@" + message.from_user.username
    else: 
        user = message.from_user.first_name + message.from_user.last_name

    user_in_team = user_exists_in_any_team(user)
    
    if user_in_team:
        bot.send_message(message.chat.id, "Вы уже в одной из команд!")
    else:
        team = teams[current_team_number]
        print(current_team_number)
        if user not in team['members']:
            team['members'].append(user)
            connection = sqlite3.connect('teams.db')
            cursor = connection.cursor()
            cursor.execute('UPDATE teams SET members = ? WHERE id = ?', (json.dumps(team['members']), team['id']))
            connection.commit()
            connection.close()
            bot.send_message(message.chat.id, "Вы успешно присоединились к команде!")
        else:
            bot.send_message(message.chat.id, "Вы уже в этой команде!")



bot.infinity_polling()
